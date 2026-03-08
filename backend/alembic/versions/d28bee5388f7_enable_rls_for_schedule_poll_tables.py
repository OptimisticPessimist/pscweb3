"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: d28bee5388f7
Revises: 7a09c18189f8
Create Date: 2026-03-09 00:45:04.905880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd28bee5388f7'
down_revision: Union[str, None] = '7a09c18189f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f'CREATE POLICY "Enable all access" ON public.{table} FOR ALL USING (true) WITH CHECK (true)')


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    tables = [
        "schedule_polls",
        "schedule_poll_candidates",
        "schedule_poll_answers",
    ]
    for table in tables:
        # ポリシーが存在する場合のみ削除するようにすることも検討できるが、
        # 既存のマイグレーションが単純な DROP POLICY なのでそれに合わせる
        op.execute(f'DROP POLICY "Enable all access" ON public.{table}')
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")

