"""出席確認スキーマ."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AttendanceStats(BaseModel):
    """出席確認統計."""
    ok: int
    ng: int
    pending: int
    total: int


class AttendanceEventResponse(BaseModel):
    """出席確認イベントレスポンス."""
    id: UUID
    project_id: UUID
    title: str
    schedule_date: datetime | None
    deadline: datetime | None
    completed: bool
    created_at: datetime
    stats: AttendanceStats


class AttendanceTargetResponse(BaseModel):
    """出席確認ターゲットレスポンス."""
    user_id: UUID
    display_name: str | None
    discord_username: str
    status: str  # "ok", "ng", "pending"


class AttendanceEventDetailResponse(BaseModel):
    """出席確認イベント詳細レスポンス."""
    id: UUID
    project_id: UUID
    title: str
    schedule_date: datetime | None
    deadline: datetime | None
    completed: bool
    created_at: datetime
    stats: AttendanceStats
    targets: list[AttendanceTargetResponse]


class AttendanceTargetUpdate(BaseModel):
    """出席確認ターゲット更新."""
    user_ids: list[str]


class AttendanceStatusUpdate(BaseModel):
    """自分の出席確認ステータス更新."""
    status: str  # "ok", "ng", "pending"
