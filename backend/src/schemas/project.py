from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """プロジェクト作成スキーマ."""

    name: str = Field(..., min_length=1, max_length=200, description="プロジェクト名")
    description: str | None = Field(None, description="説明")
    is_public: bool = Field(False, description="公開プロジェクトかどうか")
    source_public_script_id: UUID | None = Field(None, description="コピー元の公開脚本ID")


class ProjectUpdate(BaseModel):
    """プロジェクト更新スキーマ."""

    name: str | None = Field(None, min_length=1, max_length=200, description="プロジェクト名")
    description: str | None = Field(None, description="説明")
    discord_webhook_url: str | None = Field(None, description="Discord Webhook URL")
    discord_script_webhook_url: str | None = Field(None, description="脚通知用 Webhook URL")
    discord_channel_id: str | None = Field(None, description="Discord Channel ID")


class ProjectResponse(BaseModel):
    """プロジェクトレスポンス."""

    id: UUID
    name: str
    description: str | None = None
    role: str | None = None  # ユーザーの権限 (owner, editor, etc.)
    discord_webhook_url: str | None = None
    discord_script_webhook_url: str | None = None
    discord_channel_id: str | None = None
    is_public: bool = False
    is_restricted: bool = False  # 上限超過による制限モードフラグ
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    """プロジェクトメンバーレスポンス."""
    
    user_id: UUID
    discord_username: str
    role: str
    default_staff_role: str | None = None  # 基本的な役割
    display_name: str | None = None  # 表示名
    discord_avatar_url: str | None = None  # DiscordアバターURL
    joined_at: datetime
    
    model_config = {"from_attributes": True}


class MemberRoleUpdate(BaseModel):
    """メンバーロール更新リクエスト."""
    
    role: str = Field(..., pattern="^(owner|editor|viewer)$", description="新しいロール")
    default_staff_role: str | None = Field(None, description="基本的な役割（演出、照明など）")
    display_name: str | None = Field(None, description="表示名")


class MilestoneCreate(BaseModel):
    """マイルストーン作成スキーマ."""
    
    title: str = Field(..., min_length=1, max_length=200)
    start_date: datetime
    end_date: datetime | None = None
    description: str | None = None
    location: str | None = Field(None, description="場所")
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    reservation_capacity: int | None = Field(None, ge=1, description="予約定員")
    is_public: bool = Field(True, description="公開設定")
    create_attendance_check: bool = Field(False, description="出席確認を作成")
    attendance_deadline: datetime | None = Field(None, description="出席確認期限（未指定の場合はstart_dateの24時間前）")  # Simple hex validation


class MilestoneUpdate(BaseModel):
    """マイルストーン更新スキーマ."""

    title: str | None = Field(None, min_length=1, max_length=200)
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None
    location: str | None = None
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    reservation_capacity: int | None = Field(None, ge=1, description="予約定員")
    is_public: bool | None = Field(None, description="公開設定")


class MilestoneResponse(BaseModel):
    """マイルストーンレスポンス."""
    
    id: UUID
    project_id: UUID
    title: str
    start_date: datetime
    end_date: datetime | None = None
    description: str | None = None
    location: str | None = None
    color: str | None = None
    reservation_capacity: int | None = None
    current_reservation_count: int = 0
    is_public: bool | None = None
    project_name: str | None = None
    
    model_config = {"from_attributes": True}
