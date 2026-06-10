"""Restrict schedule poll RLS policies to public read access.

Revision ID: 4f6a8b2c1d3e
Revises: 7bc5f3df9821
Create Date: 2026-06-10 19:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f6a8b2c1d3e"
down_revision: str | None = "7bc5f3df9821"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLES = [
    "schedule_polls",
    "schedule_poll_candidates",
    "schedule_poll_answers",
]


def upgrade() -> None:
    """Remove unrestricted Data API writes from schedule poll tables."""
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS "Enable all access" ON public.{table}')
        op.execute(f'DROP POLICY IF EXISTS "Allow public read access" ON public.{table}')
        op.execute(
            f'CREATE POLICY "Allow public read access" ON public.{table}'
            " FOR SELECT USING (true)"
        )


def downgrade() -> None:
    """Restore the previous unrestricted policy."""
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS "Allow public read access" ON public.{table}')
        op.execute(
            f'CREATE POLICY "Enable all access" ON public.{table}'
            " FOR ALL USING (true) WITH CHECK (true)"
        )
