"""出席確認スキーマ."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    rehearsal_id: UUID | None
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
    rehearsal_id: UUID | None
    title: str
    schedule_date: datetime | None
    deadline: datetime | None
    completed: bool
    created_at: datetime
    stats: AttendanceStats
    targets: list[AttendanceTargetResponse]


class AttendanceExportTarget(BaseModel):
    """外部連携用出欠対象者."""

    name: str
    status: str


class AttendanceExportResponse(BaseModel):
    """外部連携用出欠JSONレスポンス."""

    model_config = ConfigDict(populate_by_name=True)

    schema_version: int = Field(alias="schemaVersion")
    source: str
    event_name: str = Field(alias="eventName")
    generated_at: str = Field(alias="generatedAt")
    attendances: list[AttendanceExportTarget]


class AttendanceTargetUpdate(BaseModel):
    """出席確認ターゲット更新."""

    remove_user_ids: list[str] = []
    add_user_ids: list[str] = []


class AttendanceStatusUpdate(BaseModel):
    """自分の出席確認ステータス更新."""

    status: str  # "ok", "ng", "pending"
