"""香盤表スキーマ."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CharacterInScene(BaseModel):
    """シーンに登場する人物."""

    id: UUID = Field(..., description="登場人物ID")
    name: str = Field(..., description="登場人物名")
    order: int = Field(0, description="表示順")
    is_custom: bool = Field(False, description="カスタムキャラクター")
    is_manual: bool = Field(False, description="手動追加のマッピング")

    model_config = {"from_attributes": True}


class SceneInChart(BaseModel):
    """香盤表のシーン."""

    scene_id: UUID = Field(..., description="シーンID")
    act_number: int | None = Field(None, description="幕番号")
    scene_number: int = Field(..., description="シーン番号")
    scene_heading: str = Field(..., description="シーン見出し")
    is_custom: bool = Field(False, description="カスタムシーン")
    characters: list[CharacterInScene] = Field(default_factory=list, description="登場人物リスト")


class SceneChartResponse(BaseModel):
    """香盤表レスポンス."""

    id: UUID = Field(..., description="香盤表ID")
    script_id: UUID = Field(..., description="脚本ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    scenes: list[SceneInChart] = Field(default_factory=list, description="シーンリスト")

    model_config = {"from_attributes": True}


class SceneCharacterMappingToggle(BaseModel):
    """香盤表マッピング切り替えリクエスト."""

    character_id: UUID = Field(..., description="キャラクターID")
    scene_id: UUID = Field(..., description="シーンID")


class SceneCreate(BaseModel):
    """カスタムシーン作成リクエスト."""

    heading: str = Field(..., min_length=1, max_length=200, description="シーン見出し")
    act_number: int | None = Field(None, description="幕番号")
    scene_number: int = Field(..., gt=0, description="シーン番号（1以上）")


class SceneUpdate(BaseModel):
    """シーン編集リクエスト."""

    heading: str | None = Field(None, max_length=200, description="シーン見出し")
    act_number: int | None = Field(None, description="幕番号")
    scene_number: int | None = Field(None, description="シーン番号")
