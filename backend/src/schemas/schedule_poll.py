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
    required_roles: list[str] | None = None
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
    required_roles: str | None = None  # モデルではText(str)なので
    candidates: list[SchedulePollCandidateResponse]

    model_config = ConfigDict(from_attributes=True)


class SchedulePollAnswerUpdate(SchedulePollAnswerBase):
    """日程調整回答更新."""
    pass



class SchedulePollFinalize(BaseModel):
    """日程調整確定（稽古予定作成）."""
    candidate_id: UUID
    scene_ids: list[UUID]


class SceneAvailability(BaseModel):
    """シーンの参加可否状況."""
    scene_id: UUID
    scene_number: int
    heading: str
    is_possible: bool  # 必須キャスト全員が OK または Maybe
    is_reach: bool = False  # あと1人で可能
    missing_user_names: list[str] = []
    reason: str | None = None


class PollCandidateAnalysis(BaseModel):
    """候補日程の分析結果."""
    candidate_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    possible_scenes: list[SceneAvailability]
    reach_scenes: list[SceneAvailability]
    available_users: list[UUID]  # OK または Maybe のユーザーID
    maybe_users: list[UUID]      # Maybe のユーザーID（色分け用）
    available_user_names: list[str] = []
    maybe_user_names: list[str] = []


class SchedulePollCalendarAnalysis(BaseModel):
    """日程調整全体のカレンダー用分析結果."""
    poll_id: UUID
    analyses: list[PollCandidateAnalysis]
