"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: 9660d389e8f0
Revises: 43eb847cfc0a
Create Date: 2026-01-09 13:39:43.018365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9660d389e8f0'
down_revision: Union[str, None] = '43eb847cfc0a'
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
        "attendance_targets",
        "scenes",
        "characters",
        "scene_charts",
        "rehearsal_schedules",
        "scene_character_mappings",
        "character_castings",
        "lines",
        "rehearsals",
        "rehearsal_scenes",
        "rehearsal_participants",
        "rehearsal_casts",
        "reservations",
    ]
    
    # 既存の "Enable all access" ポリシーを削除し、SELECT のみのポリシーを作成
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS "Enable all access" ON public.{table}')
        op.execute(f'CREATE POLICY "Allow public read access" ON public.{table} FOR SELECT USING (true)')

    # alembic_version は読み取りも制限する（ポリシー削除のみ）
    op.execute('DROP POLICY IF EXISTS "Enable all access" ON public.alembic_version')


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
        "attendance_targets",
        "scenes",
        "characters",
        "scene_charts",
        "rehearsal_schedules",
        "scene_character_mappings",
        "character_castings",
        "lines",
        "rehearsals",
        "rehearsal_scenes",
        "rehearsal_participants",
        "rehearsal_casts",
        "reservations",
        "alembic_version",
    ]
    
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS "Allow public read access" ON public.{table}')
        op.execute(f'DROP POLICY IF EXISTS "Enable all access" ON public.{table}')
        op.execute(f'CREATE POLICY "Enable all access" ON public.{table} FOR ALL USING (true) WITH CHECK (true)')
