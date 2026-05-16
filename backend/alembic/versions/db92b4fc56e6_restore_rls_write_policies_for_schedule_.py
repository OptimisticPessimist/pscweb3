"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: db92b4fc56e6
Revises: 8556f52c33e9
Create Date: 2026-04-15 22:04:24.123429

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db92b4fc56e6"
down_revision: str | None = "8556f52c33e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """日程調整テーブルのRLSポリシーを修正し、書き込み権限を復元する.

    ce7cc9d0b71f でSELECTのみに制限されていたポリシーを
    他テーブルと同じ FOR ALL に戻す。
    これにより INSERT/UPDATE/DELETE がブロックされていた問題を修正する。
    """
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        # SELECTのみのポリシーを削除
        op.execute(f'DROP POLICY IF EXISTS "Enable read access for all" ON public.{table}')
        # 全操作を許可するポリシーを再作成（他テーブルと同じパターン）
        op.execute(
            f'CREATE POLICY "Enable all access" ON public.{table}'
            f" FOR ALL USING (true) WITH CHECK (true)"
        )


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS "Enable all access" ON public.{table}')
        op.execute(
            f'CREATE POLICY "Enable read access for all" ON public.{table}'
            f" FOR SELECT USING (true)"
        )
