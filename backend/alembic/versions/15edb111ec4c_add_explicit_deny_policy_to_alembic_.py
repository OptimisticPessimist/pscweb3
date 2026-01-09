"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: 15edb111ec4c
Revises: 9660d389e8f0
Create Date: 2026-01-09 13:47:45.208836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15edb111ec4c'
down_revision: Union[str, None] = '9660d389e8f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    # RLSが有効な状態でポリシーがないことによる警告を避けるため、明示的に「常に拒否」するポリシーを追加
    op.execute('CREATE POLICY "Explicitly deny all public access" ON public.alembic_version FOR ALL USING (false) WITH CHECK (false)')


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    op.execute('DROP POLICY IF EXISTS "Explicitly deny all public access" ON public.alembic_version')
