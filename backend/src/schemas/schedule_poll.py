"""日程調整スキーマ."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SchedulePollAnswerBase(BaseModel):
    """日程調整回答ベース."""
    status: str  # "ok", "maybe", "ng"


class SchedulePollAnswerResponse(SchedulePollAnswerBase):
    """日程調整回答レスポンス."""
    user_id: UUID
    display_name: str | None = None
    discord_username: str | None = None
    role: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SchedulePollCandidateBase(BaseModel):
    """日程調整候補ベース."""
    start_datetime: datetime
    end_datetime: datetime


class SchedulePollCandidateCreate(SchedulePollCandidateBase):
    """日程調整候補作成."""
    pass


class SchedulePollCandidateResponse(SchedulePollCandidateBase):
    """日程調整候補レスポンス."""
    id: UUID
    poll_id: UUID
    answers: list[SchedulePollAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SchedulePollCreate(BaseModel):
    """日程調整作成."""
    title: str
    description: str | None = None
    candidates: list[SchedulePollCandidateCreate]


class SchedulePollResponse(BaseModel):
    """日程調整レスポンス."""
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    is_closed: bool
    created_at: datetime
    creator_id: UUID
    candidates: list[SchedulePollCandidateResponse]

    model_config = ConfigDict(from_attributes=True)


class SchedulePollAnswerUpdate(SchedulePollAnswerBase):
    """日程調整回答更新."""
    pass


class SchedulePollFinalize(BaseModel):
    """日程調整確定（稽古予定作成）."""
    candidate_id: UUID
    scene_ids: list[UUID]
