"""Pydanticスキーマ - 脚本関連."""

from datetime import datetime

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):
    """登場人物レスポンス."""

    id: int = Field(..., description="登場人物ID")
    name: str = Field(..., description="登場人物名")

    model_config = {"from_attributes": True}


class LineResponse(BaseModel):
    """セリフレスポンス."""

    id: int = Field(..., description="セリフID")
    character: CharacterResponse = Field(..., description="登場人物")
    content: str = Field(..., description="セリフ内容")
    order: int = Field(..., description="順番")

    model_config = {"from_attributes": True}


class SceneResponse(BaseModel):
    """シーンレスポンス."""

    id: int = Field(..., description="シーンID")
    scene_number: int = Field(..., description="シーン番号")
    heading: str = Field(..., description="見出し")
    description: str | None = Field(None, description="説明")
    lines: list[LineResponse] = Field(default_factory=list, description="セリフリスト")

    model_config = {"from_attributes": True}


class ScriptResponse(BaseModel):
    """脚本レスポンス."""

    id: int = Field(..., description="脚本ID")
    project_id: int = Field(..., description="プロジェクトID")
    title: str = Field(..., description="タイトル")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    characters: list[CharacterResponse] = Field(
        default_factory=list, description="登場人物リスト"
    )
    scenes: list[SceneResponse] = Field(default_factory=list, description="シーンリスト")

    model_config = {"from_attributes": True}


class ScriptListResponse(BaseModel):
    """脚本一覧レスポンス（詳細なし）."""

    id: int = Field(..., description="脚本ID")
    project_id: int = Field(..., description="プロジェクトID")
    title: str = Field(..., description="タイトル")
    uploaded_at: datetime = Field(..., description="アップロード日時")

    model_config = {"from_attributes": True}
