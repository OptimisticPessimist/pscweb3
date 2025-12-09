"""香盤表スキーマ."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CharacterInScene(BaseModel):
    """シーンに登場する人物."""

    id: UUID = Field(..., description="登場人物ID")
    name: str = Field(..., description="登場人物名")

    model_config = {"from_attributes": True}


class SceneInChart(BaseModel):
    """香盤表のシーン."""

    act_number: int | None = Field(None, description="幕番号")
    scene_number: int = Field(..., description="シーン番号")
    scene_heading: str = Field(..., description="シーン見出し")
    characters: list[CharacterInScene] = Field(
        default_factory=list, description="登場人物リスト"
    )


class SceneChartResponse(BaseModel):
    """香盤表レスポンス."""

    id: UUID = Field(..., description="香盤表ID")
    script_id: UUID = Field(..., description="脚本ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    scenes: list[SceneInChart] = Field(default_factory=list, description="シーンリスト")

    model_config = {"from_attributes": True}
