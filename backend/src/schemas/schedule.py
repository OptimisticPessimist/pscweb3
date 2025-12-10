from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduleItem(BaseModel):
    """スケジュールアイテムの共通基底クラス."""

    id: UUID
    type: Literal["rehearsal", "milestone"]
    title: str
    date: datetime = Field(..., description="開始日時")
    end_date: datetime | None = Field(None, description="終了日時")
    project_id: UUID
    project_name: str
    description: str | None = None

    # Rehearsal specific
    location: str | None = None
    scene_heading: str | None = None

    # Milestone specific
    color: str | None = None

class UserScheduleResponse(BaseModel):
    """ユーザースケジュールレスポンス."""
    items: list[ScheduleItem]
