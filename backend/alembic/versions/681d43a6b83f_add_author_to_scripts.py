"""add author to scripts

Revision ID: 681d43a6b83f
Revises: e44101c53df8
Create Date: 2025-12-13 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '681d43a6b83f'
down_revision: Union[str, None] = 'e44101c53df8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scripts', sa.Column('author', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('scripts', 'author')
