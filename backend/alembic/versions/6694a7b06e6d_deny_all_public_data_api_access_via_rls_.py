"""Deny all public Data API access via RLS on all application tables.

Supabase の Data API (PostgREST / anon キー) は public スキーマのテーブルを
外部へ公開する。これまでのマイグレーションでは各テーブルに
``USING (true)`` の SELECT ポリシーが残っており、anon キーさえあれば
``reservations`` の氏名・メール、``users`` の Discord ID、``scripts`` の
脚本全文、``audit_logs`` の IP アドレスなどが誰でも読めてしまう。

アプリケーションは Supabase クライアントを一切使わず、すべての DB 操作は
バックエンドが所有者ロール (RLS をバイパス) で行うため、公開ポリシーは
機能上不要である。そこで alembic_version と同様の「明示的な全拒否」
ポリシーへ統一し、Data API 経由の読み書きを全テーブルで遮断する。

RLS は所有者ロールには (FORCE しない限り) 適用されないため、
バックエンドの動作には影響しない。

Revision ID: 6694a7b06e6d
Revises: 4f6a8b2c1d3e
Create Date: 2026-06-10 22:52:39.632377

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6694a7b06e6d"
down_revision: str | None = "4f6a8b2c1d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# アプリケーションが利用する public スキーマの全テーブル
TABLES = [
    "users",
    "theater_projects",
    "project_members",
    "scripts",
    "scenes",
    "characters",
    "lines",
    "scene_charts",
    "scene_character_mappings",
    "character_castings",
    "notification_settings",
    "rehearsal_schedules",
    "rehearsals",
    "rehearsal_scenes",
    "rehearsal_participants",
    "rehearsal_casts",
    "project_invitations",
    "audit_logs",
    "milestones",
    "reservations",
    "attendance_events",
    "attendance_targets",
    "schedule_polls",
    "schedule_poll_candidates",
    "schedule_poll_answers",
]

DENY_POLICY = "Explicitly deny all public access"


def upgrade() -> None:
    """全テーブルで Data API 経由の公開アクセスを拒否する."""
    for table in TABLES:
        # RLS を確実に有効化（既に有効でも冪等）
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        # 名称が履歴で揺れている既存ポリシーを名前に依存せず全削除し、
        # 許可ポリシーの残存（PERMISSIVE は OR 結合される）を防ぐ
        op.execute(
            f"""
            DO $$
            DECLARE
                policy_name text;
            BEGIN
                FOR policy_name IN
                    SELECT policyname FROM pg_policies
                    WHERE schemaname = 'public' AND tablename = '{table}'
                LOOP
                    EXECUTE format('DROP POLICY %I ON public.{table}', policy_name);
                END LOOP;
            END $$;
            """
        )
        # 明示的な全拒否ポリシー（RLS 有効＋ポリシー無しの警告も回避）
        op.execute(
            f'CREATE POLICY "{DENY_POLICY}" ON public.{table} '
            f"FOR ALL USING (false) WITH CHECK (false)"
        )


def downgrade() -> None:
    """直前の状態（SELECT のみ公開）へ戻す."""
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS "{DENY_POLICY}" ON public.{table}')
        op.execute(
            f'CREATE POLICY "Allow public read access" ON public.{table} '
            f"FOR SELECT USING (true)"
        )
