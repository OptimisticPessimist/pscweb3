"""add rehearsal_id to attendance_events

Revision ID: a1b2c3d4e5f6
Revises: 6694a7b06e6d
Create Date: 2026-06-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "6694a7b06e6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "attendance_events",
        sa.Column("rehearsal_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_attendance_events_rehearsal_id",
        "attendance_events",
        ["rehearsal_id"],
    )
    op.create_foreign_key(
        "fk_attendance_events_rehearsal_id",
        "attendance_events",
        "rehearsals",
        ["rehearsal_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 既存データのバックフィル: schedule_date が rehearsal の date と一致する場合に紐付ける
    op.execute("""
        UPDATE attendance_events ae
        SET rehearsal_id = r.id
        FROM rehearsals r
        JOIN rehearsal_schedules rs ON r.schedule_id = rs.id
        WHERE rs.project_id = ae.project_id
          AND ae.schedule_date IS NOT NULL
          AND ABS(EXTRACT(EPOCH FROM (ae.schedule_date - r.date))) < 1
          AND ae.rehearsal_id IS NULL
    """)


def downgrade() -> None:
    op.drop_constraint(
        "fk_attendance_events_rehearsal_id", "attendance_events", type_="foreignkey"
    )
    op.drop_index("ix_attendance_events_rehearsal_id", table_name="attendance_events")
    op.drop_column("attendance_events", "rehearsal_id")
