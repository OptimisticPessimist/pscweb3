"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: ce7cc9d0b71f
Revises: ab6eb8af6b2b
Create Date: 2026-03-09 22:44:39.419752

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce7cc9d0b71f"
down_revision: str | None = "ab6eb8af6b2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        # 既存の過剰なポリシーを削除
        op.execute(f'DROP POLICY IF EXISTS "Enable all access" ON public.{table}')
        # SELECTのみを許可するポリシーを作成（これは警告対象外）
        op.execute(
            f'CREATE POLICY "Enable read access for all" ON public.{table} FOR SELECT USING (true)'
        )


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        # SELECTのみのポリシーを削除
        op.execute(f'DROP POLICY IF EXISTS "Enable read access for all" ON public.{table}')
        # 元の過剰なポリシーを再作成
        op.execute(
            f'CREATE POLICY "Enable all access" ON public.{table} FOR ALL USING (true) WITH CHECK (true)'
        )
