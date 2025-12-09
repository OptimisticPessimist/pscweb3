"""Pydanticスキーマ - 脚本関連."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):
    """登場人物レスポンス."""

    id: UUID = Field(..., description="登場人物ID")
    name: str = Field(..., description="登場人物名")

    model_config = {"from_attributes": True}


class LineResponse(BaseModel):
    """セリフレスポンス."""

    id: UUID = Field(..., description="セリフID")
    character: CharacterResponse = Field(..., description="登場人物")
    content: str = Field(..., description="セリフ内容")
    order: int = Field(..., description="順番")

    model_config = {"from_attributes": True}


class SceneResponse(BaseModel):
    """シーンレスポンス."""

    id: UUID = Field(..., description="シーンID")
    act_number: int | None = Field(None, description="幕番号")
    scene_number: int = Field(..., description="シーン番号")
    heading: str = Field(..., description="見出し")
    description: str | None = Field(None, description="説明")
    lines: list[LineResponse] = Field(default_factory=list, description="セリフリスト")

    model_config = {"from_attributes": True}


class ScriptResponse(BaseModel):
    """脚本レスポンス."""

    id: UUID = Field(..., description="脚本ID")
    project_id: UUID = Field(..., description="プロジェクトID")
    title: str = Field(..., description="タイトル")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    revision: int = Field(default=1, description="リビジョン番号")
    characters: list[CharacterResponse] = Field(
        default_factory=list, description="登場人物リスト"
    )
    scenes: list[SceneResponse] = Field(default_factory=list, description="シーンリスト")

    model_config = {"from_attributes": True}


class ScriptSummary(BaseModel):
    """脚本一覧レスポンス（詳細なし - 単体）."""

    id: UUID = Field(..., description="脚本ID")
    project_id: UUID = Field(..., description="プロジェクトID")
    title: str = Field(..., description="タイトル")
    uploaded_at: datetime = Field(..., description="アップロード日時")
    revision: int = Field(default=1, description="リビジョン番号")

    model_config = {"from_attributes": True}


class ScriptListResponse(BaseModel):
    """脚本一覧レスポンスWrapper."""
    scripts: list[ScriptSummary] = Field(..., description="脚本リスト")
