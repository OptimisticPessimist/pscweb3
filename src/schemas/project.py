from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """プロジェクト作成リクエスト."""

    name: str = Field(..., description="プロジェクト名")
    description: str | None = Field(None, description="説明")


class ProjectResponse(BaseModel):
    """プロジェクトレスポンス."""

    id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    description: str | None = Field(None, description="説明")
    discord_webhook_url: str | None = Field(None, description="Discord Webhook URL")
    created_at: datetime = Field(..., description="作成日時")
    role: str | None = Field(None, description="ユーザーのロール (一覧取得時など)")

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    """プロジェクトメンバーレスポンス."""
    
    user_id: int
    discord_username: str
    role: str
    joined_at: datetime
    
    model_config = {"from_attributes": True}


class MemberRoleUpdate(BaseModel):
    """メンバーロール更新リクエスト."""
    
    role: str = Field(..., pattern="^(owner|editor|viewer)$", description="新しいロール")
