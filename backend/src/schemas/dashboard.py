"""ダッシュボードスキーマ."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActivityItem(BaseModel):
    """アクティビティアイテム."""
    
    type: str  # "script_upload", "milestone_created", etc.
    title: str
    description: str | None = None
    timestamp: datetime
    user_name: str | None = None


class RehearsalInfo(BaseModel):
    """稽古情報（簡易版）."""
    
    id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None


class MilestoneInfo(BaseModel):
    """マイルストーン情報（簡易版）."""
    
    id: UUID
    title: str
    start_date: datetime
    end_date: datetime | None = None
    location: str | None = None
    days_until: int  # 残り日数


class DashboardResponse(BaseModel):
    """ダッシュボードレスポンス."""
    
    next_rehearsal: RehearsalInfo | None = None
    next_milestone: MilestoneInfo | None = None
    pending_attendance_count: int = 0
    total_members: int = 0
    recent_activities: list[ActivityItem] = []
    
    model_config = {"from_attributes": True}
