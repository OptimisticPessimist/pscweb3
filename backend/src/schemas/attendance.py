"""出席確認APIのスキーマ定義."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceStats(BaseModel):
    """出席状況の集計."""
    
    ok: int = 0
    ng: int = 0
    pending: int = 0
    total: int = 0


class AttendanceTargetResponse(BaseModel):
    """出席確認対象者のレスポンススキーマ."""
    
    user_id: UUID
    display_name: str | None = None
    discord_username: str | None = None
    status: str  # ok, ng, pending


class AttendanceEventResponse(BaseModel):
    """出席イベントのレスポンススキーマ."""
    
    id: UUID
    project_id: UUID
    title: str
    schedule_date: datetime | None = None
    deadline: datetime
    completed: bool
    created_at: datetime
    stats: AttendanceStats


class AttendanceEventDetailResponse(AttendanceEventResponse):
    """出席イベント詳細のレスポンススキーマ."""
    
    targets: list[AttendanceTargetResponse]


class AttendanceTargetUpdate(BaseModel):
    """出席確認対象者の更新リクエストスキーマ."""
    
    add_user_ids: list[str] = Field(default_factory=list)
    remove_user_ids: list[str] = Field(default_factory=list)
