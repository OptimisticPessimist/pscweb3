"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: d2f1bd30103f
Revises: c0e567c6f687
Create Date: 2025-12-09 01:17:19.755861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f1bd30103f'
down_revision: Union[str, None] = 'c0e567c6f687'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    pass


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    pass
