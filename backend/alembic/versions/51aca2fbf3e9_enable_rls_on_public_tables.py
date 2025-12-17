"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: 51aca2fbf3e9
Revises: 681d43a6b83f
Create Date: 2025-12-17 19:50:49.436438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51aca2fbf3e9'
down_revision: Union[str, None] = '681d43a6b83f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    tables = [
        "project_members",
        "theater_projects",
        "users",
        "notification_settings",
        "project_invitations",
        "scripts",
        "audit_logs",
        "milestones",
        "attendance_events",
        "scenes",
        "characters",
        "scene_charts",
        "rehearsal_schedules",
        "scene_character_mappings",
        "character_castings",
        "attendance_targets",
        "lines",
        "rehearsals",
        "rehearsal_scenes",
        "rehearsal_participants",
        "rehearsal_casts",
    ]
    for table in tables:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f'CREATE POLICY "Enable all access" ON public.{table} FOR ALL USING (true) WITH CHECK (true)')


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    tables = [
        "project_members",
        "theater_projects",
        "users",
        "notification_settings",
        "project_invitations",
        "scripts",
        "audit_logs",
        "milestones",
        "attendance_events",
        "scenes",
        "characters",
        "scene_charts",
        "rehearsal_schedules",
        "scene_character_mappings",
        "character_castings",
        "attendance_targets",
        "lines",
        "rehearsals",
        "rehearsal_scenes",
        "rehearsal_participants",
        "rehearsal_casts",
    ]
    for table in tables:
        op.execute(f'DROP POLICY "Enable all access" ON public.{table}')
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
