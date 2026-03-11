"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: af05603d867c
Revises: fc4412ef54dc
Create Date: 2025-12-29 10:55:31.411981

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af05603d867c"
down_revision: str | None = "fc4412ef54dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    op.add_column(
        "milestones", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true")
    )


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    op.drop_column("milestones", "is_public")
