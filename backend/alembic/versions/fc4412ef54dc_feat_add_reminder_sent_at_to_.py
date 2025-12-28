"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: fc4412ef54dc
Revises: 26dbc6dee525
Create Date: 2025-12-29 04:24:26.806676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc4412ef54dc'
down_revision: Union[str, None] = '26dbc6dee525'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    # reservationsテーブルにreminder_sent_atカラムを追加
    op.add_column('reservations', sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    # reservationsテーブルからreminder_sent_atカラムを削除
    op.drop_column('reservations', 'reminder_sent_at')
