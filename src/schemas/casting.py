"""キャスティングスキーマ."""

from pydantic import BaseModel, Field


class CharacterCastingCreate(BaseModel):
    """キャスト割り当てリクエスト."""

    user_id: int = Field(..., description="ユーザーID")
    cast_name: str | None = Field(None, description="キャスト名（Aキャスト、Bキャストなど）")


class CharacterCastingResponse(BaseModel):
    """キャスト割り当てレスポンス."""

    id: int = Field(..., description="キャスティングID")
    character_id: int = Field(..., description="登場人物ID")
    character_name: str = Field(..., description="登場人物名")
    user_id: int = Field(..., description="ユーザーID")
    user_name: str = Field(..., description="ユーザー名")
    cast_name: str | None = Field(None, description="キャスト名")

    model_config = {"from_attributes": True}


class ScriptCastingResponse(BaseModel):
    """脚本全体のキャスト一覧."""

    script_id: int = Field(..., description="脚本ID")
    script_title: str = Field(..., description="脚本タイトル")
    castings: list[CharacterCastingResponse] = Field(
        default_factory=list, description="キャスト一覧"
    )
