"""Pydanticスキーマ - 認証関連."""

from uuid import UUID
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """ユーザー情報レスポンス."""

    id: UUID = Field(..., description="ユーザーID")
    discord_id: str = Field(..., description="Discord ユーザーID")
    discord_username: str = Field(..., description="Discord ユーザー名")
    screen_name: str | None = Field(None, description="スクリーンネーム")
    discord_avatar_url: str | None = Field(None, description="Discordアバター画像URL")

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user):
        """UserモデルからUserResponseを生成."""
        return cls(
            id=user.id,
            discord_id=user.discord_id,
            discord_username=user.discord_username,
            screen_name=user.screen_name,
            discord_avatar_url=user.discord_avatar_url
        )


class TokenResponse(BaseModel):
    """JWT トークンレスポンス."""

    access_token: str = Field(..., description="アクセストークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
