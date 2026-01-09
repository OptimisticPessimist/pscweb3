"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: 43eb847cfc0a
Revises: b6f8db84f1db
Create Date: 2026-01-09 13:13:28.954971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43eb847cfc0a'
down_revision: Union[str, None] = 'b6f8db84f1db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    op.execute("ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY")
    op.execute('CREATE POLICY "Enable all access" ON public.reservations FOR ALL USING (true) WITH CHECK (true)')


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    op.execute('DROP POLICY "Enable all access" ON public.reservations')
    op.execute("ALTER TABLE public.reservations DISABLE ROW LEVEL SECURITY")
