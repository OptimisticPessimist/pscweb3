"""add_metadata_to_scripts

Revision ID: b6f8db84f1db
Revises: af05603d867c
Create Date: 2025-12-29 15:02:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6f8db84f1db"
down_revision: str | None = "af05603d867c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # scriptsテーブルにメタデータカラムを追加
    op.add_column("scripts", sa.Column("draft_date", sa.String(length=100), nullable=True))
    op.add_column("scripts", sa.Column("copyright", sa.String(length=200), nullable=True))
    op.add_column("scripts", sa.Column("contact", sa.Text(), nullable=True))
    op.add_column("scripts", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("scripts", sa.Column("revision_text", sa.String(length=200), nullable=True))


def downgrade() -> None:
    # scriptsテーブルからメタデータカラムを削除
    op.drop_column("scripts", "revision_text")
    op.drop_column("scripts", "notes")
    op.drop_column("scripts", "contact")
    op.drop_column("scripts", "copyright")
    op.drop_column("scripts", "draft_date")
