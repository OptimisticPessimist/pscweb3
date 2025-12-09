"""キャラクターおよびキャスティング関連のスキーマ."""

from uuid import UUID
from pydantic import BaseModel, Field

class CastingUser(BaseModel):
    """配役されたユーザー情報."""
    user_id: UUID = Field(..., description="ユーザーID")
    discord_username: str = Field(..., description="Discordユーザー名")
    display_name: str | None = Field(None, description="プロジェクト内表示名")
    cast_name: str | None = Field(None, description="Memo (Pattern A etc.)")

    model_config = {"from_attributes": True}

class CharacterResponse(BaseModel):
    """キャラクター詳細（キャスティング情報含む）."""
    id: UUID = Field(..., description="キャラクターID")
    name: str = Field(..., description="キャラクター名")
    castings: list[CastingUser] = Field(default_factory=list, description="配役リスト")

    model_config = {"from_attributes": True}

class CastingCreate(BaseModel):
    """配役追加リクエスト."""
    user_id: UUID = Field(..., description="ユーザーID")
    cast_name: str | None = Field(None, description="Memo (Pattern A etc.)")

class CastingDelete(BaseModel):
    """配役解除リクエスト."""
    user_id: UUID = Field(..., description="ユーザーID")
