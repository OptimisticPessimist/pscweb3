"""Pydanticスキーマ - 認証関連."""

from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """ユーザー情報レスポンス."""

    id: UUID = Field(..., description="ユーザーID")
    discord_id: str = Field(..., description="Discord ユーザーID")
    discord_username: str = Field(..., description="Discord ユーザー名")
    email: str | None = Field(None, description="メールアドレス")
    display_name: str | None = Field(None, description="表示名（Global Name）")
    avatar_url: str | None = Field(None, description="アバター画像URL")

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT トークンレスポンス."""

    access_token: str = Field(..., description="アクセストークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
