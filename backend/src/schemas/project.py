from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """プロジェクト作成スキーマ."""

    name: str = Field(..., min_length=1, max_length=200, description="プロジェクト名")
    description: str | None = Field(None, description="説明")


class ProjectResponse(BaseModel):
    """プロジェクトレスポンス."""

    id: UUID
    name: str
    description: str | None = None
    role: str | None = None  # ユーザーの権限 (owner, editor, etc.)
    discord_webhook_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    """プロジェクトメンバーレスポンス."""
    
    user_id: UUID
    discord_username: str
    role: str
    default_staff_role: str | None = None  # 基本的な役割
    display_name: str | None = None  # 表示名
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
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")  # Simple hex validation


class MilestoneResponse(BaseModel):
    """マイルストーンレスポンス."""
    
    id: UUID
    project_id: UUID
    title: str
    start_date: datetime
    end_date: datetime | None = None
    description: str | None = None
    color: str | None = None
    
    model_config = {"from_attributes": True}
