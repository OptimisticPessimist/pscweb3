"""稽古スケジュールスキーマ."""

from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, Field


class RehearsalParticipantResponse(BaseModel):
    """稽古参加者レスポンス."""

    user_id: UUID = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")
    display_name: str | None = Field(None, description="プロジェクト内表示名")
    staff_role: str | None = Field(None, description="役割（演出、照明など）")

    model_config = {"from_attributes": True}


class RehearsalCastResponse(BaseModel):
    """稽古キャストレスポンス."""

    character_id: UUID = Field(..., description="登場人物ID")
    character_name: str = Field(..., description="登場人物名")
    user_id: UUID = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")
    display_name: str | None = Field(None, description="プロジェクト内表示名")

    model_config = {"from_attributes": True}


class RehearsalCastCreate(BaseModel):
    """稽古キャスト追加リクエスト."""

    character_id: UUID = Field(..., description="登場人物ID")
    user_id: UUID = Field(..., description="ユーザーID")


class RehearsalResponse(BaseModel):
    """稽古レスポンス."""

    id: UUID = Field(..., description="稽古ID")
    schedule_id: UUID = Field(..., description="スケジュールID")
    scene_id: UUID | None = Field(None, description="シーンID")
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


class RehearsalParticipantCreate(BaseModel):
    """稽古参加者作成リクエスト."""

    user_id: UUID = Field(..., description="ユーザーID")
    staff_role: str | None = Field(None, description="役割")


class RehearsalCastCreate(BaseModel):
    """稽古キャスト作成リクエスト."""

    user_id: UUID = Field(..., description="ユーザーID")
    character_id: UUID = Field(..., description="キャラクターID")


class RehearsalCreate(BaseModel):
    """稽古作成リクエスト."""

    scene_id: UUID | None = Field(None, description="シーンID（非推奨: scene_idsを使用してください）")
    scene_ids: list[UUID] = Field(default_factory=list, description="シーンIDリスト")
    date: datetime = Field(..., description="稽古日時")
    duration_minutes: int = Field(120, description="稽古時間（分）")
    location: str | None = Field(None, description="場所")
    notes: str | None = Field(None, description="備考")
    create_attendance_check: bool = Field(False, description="出席確認を作成")
    attendance_deadline: datetime | None = Field(None, description="出席確認期限（未指定の場合は稽古日の24時間前）")
    
    # 参加者・キャストの明示的な指定（指定がない場合は自動決定ロジックが走る場合があるが、基本はFrontendから送る）
    participants: list[RehearsalParticipantCreate] | None = Field(None, description="スタッフ参加者リスト")
    casts: list[RehearsalCastCreate] | None = Field(None, description="キャスト参加者リスト")


class RehearsalUpdate(BaseModel):
    """稽古更新リクエスト."""

    scene_id: UUID | None = Field(None, description="シーンID（非推奨）")
    scene_ids: list[UUID] | None = Field(None, description="シーンIDリスト")
    date: datetime | None = Field(None, description="稽古日時")
    duration_minutes: int | None = Field(None, description="稽古時間（分）")
    location: str | None = Field(None, description="場所")
    notes: str | None = Field(None, description="備考")
    participants: list[RehearsalParticipantCreate] | None = Field(None, description="スタッフ参加者リスト")
    casts: list[RehearsalCastCreate] | None = Field(None, description="キャスト参加者リスト")


class RehearsalParticipantUpdate(BaseModel):
    """参加者役割更新リクエスト."""

    staff_role: str | None = Field(None, description="役割（演出、照明など）")


class RehearsalScheduleResponse(BaseModel):
    """稽古スケジュールレスポンス."""

    id: UUID = Field(..., description="スケジュールID")
    project_id: UUID = Field(..., description="プロジェクトID")
    script_id: UUID = Field(..., description="脚本ID")
    script_title: str = Field(..., description="脚本タイトル")
    created_at: datetime = Field(..., description="作成日時")
    rehearsals: list[RehearsalResponse] = Field(
        default_factory=list, description="稽古一覧"
    )

    model_config = {"from_attributes": True}
