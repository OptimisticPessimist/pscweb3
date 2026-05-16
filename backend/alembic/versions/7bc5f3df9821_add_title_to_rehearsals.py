"""Add title column to rehearsals.

Revision ID: 7bc5f3df9821
Revises: db92b4fc56e6
Create Date: 2026-05-16 11:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7bc5f3df9821"
down_revision: str | None = "db92b4fc56e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade migration."""
    op.add_column("rehearsals", sa.Column("title", sa.String(length=200), nullable=True))


def downgrade() -> None:
    """Downgrade migration."""
    op.drop_column("rehearsals", "title")
