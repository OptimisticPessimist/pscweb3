"""稽古スケジュールスキーマ."""

from datetime import datetime

from pydantic import BaseModel, Field


class RehearsalParticipantResponse(BaseModel):
    """稽古参加者レスポンス."""

    user_id: int = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")

    model_config = {"from_attributes": True}


class RehearsalCastResponse(BaseModel):
    """稽古キャストレスポンス."""

    character_id: int = Field(..., description="登場人物ID")
    character_name: str = Field(..., description="登場人物名")
    user_id: int = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")

    model_config = {"from_attributes": True}


class RehearsalResponse(BaseModel):
    """稽古レスポンス."""

    id: int = Field(..., description="稽古ID")
    schedule_id: int = Field(..., description="スケジュールID")
    scene_id: int | None = Field(None, description="シーンID")
    scene_heading: str | None = Field(None, description="シーン見出し")
    date: datetime = Field(..., description="稽古日時")
    duration_minutes: int = Field(..., description="稽古時間（分）")
    location: str | None = Field(None, description="場所")
    notes: str | None = Field(None, description="備考")
    participants: list[RehearsalParticipantResponse] = Field(
        default_factory=list, description="参加者一覧"
    )
    casts: list[RehearsalCastResponse] = Field(
        default_factory=list, description="キャスト一覧"
    )


class RehearsalCreate(BaseModel):
    """稽古作成リクエスト."""

    scene_id: int | None = Field(None, description="シーンID")
    date: datetime = Field(..., description="稽古日時")
    duration_minutes: int = Field(120, description="稽古時間（分）")
    location: str | None = Field(None, description="場所")
    notes: str | None = Field(None, description="備考")


class RehearsalUpdate(BaseModel):
    """稽古更新リクエスト."""

    scene_id: int | None = Field(None, description="シーンID")
    date: datetime | None = Field(None, description="稽古日時")
    duration_minutes: int | None = Field(None, description="稽古時間（分）")
    location: str | None = Field(None, description="場所")
    notes: str | None = Field(None, description="備考")


class RehearsalScheduleResponse(BaseModel):
    """稽古スケジュールレスポンス."""

    id: int = Field(..., description="スケジュールID")
    project_id: int = Field(..., description="プロジェクトID")
    script_id: int = Field(..., description="脚本ID")
    script_title: str = Field(..., description="脚本タイトル")
    created_at: datetime = Field(..., description="作成日時")
    rehearsals: list[RehearsalResponse] = Field(
        default_factory=list, description="稽古一覧"
    )

    model_config = {"from_attributes": True}
