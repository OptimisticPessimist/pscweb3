"""Add schedule poll targets.

Revision ID: 9f3b2c7d1a84
Revises: 4f6a8b2c1d3e
Create Date: 2026-07-05 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f3b2c7d1a84"
down_revision: str | None = "4f6a8b2c1d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create target table for schedule polls."""
    op.create_table(
        "schedule_poll_targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("poll_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["poll_id"], ["schedule_polls.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("poll_id", "user_id", name="uq_schedule_poll_target_user"),
    )
    op.execute("ALTER TABLE public.schedule_poll_targets ENABLE ROW LEVEL SECURITY")
    op.execute(
        'CREATE POLICY "Enable all access" ON public.schedule_poll_targets'
        " FOR ALL USING (true) WITH CHECK (true)"
    )


def downgrade() -> None:
    """Drop target table for schedule polls."""
    op.execute('DROP POLICY IF EXISTS "Enable all access" ON public.schedule_poll_targets')
    op.drop_table("schedule_poll_targets")
