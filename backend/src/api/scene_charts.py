"""香盤表APIエンドポイント."""

import uuid as uuid_mod
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    Character,
    ProjectMember,
    Scene,
    SceneCharacterMapping,
    SceneChart,
    Script,
)
from src.dependencies.permissions import get_project_editor_dep, get_project_member_dep, get_script_member_dep
from src.schemas.scene_chart import (
    CharacterInScene,
    SceneCharacterMappingToggle,
    SceneChartResponse,
    SceneCreate,
    SceneInChart,
    SceneUpdate,
)
from src.services.scene_chart_generator import generate_scene_chart

router = APIRouter()
project_router = APIRouter()


# ===========================
# 既存エンドポイント (scriptベース)
# ===========================


@router.post("/{script_id}/generate-scene-chart", response_model=SceneChartResponse)
async def create_scene_chart(
    script_id: UUID,
    member_and_script: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """脚本から香盤表を自動生成."""
    member, script = member_and_script
    chart = await generate_scene_chart(script, db)
    await db.commit()
    await db.refresh(chart)
    return await _build_scene_chart_response(chart, script, db)


@router.get("/{script_id}/scene-chart", response_model=SceneChartResponse)
async def get_scene_chart(
    script_id: UUID,
    member_and_script: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """香盤表を取得."""
    member, script = member_and_script

    result = await db.execute(
        select(SceneChart)
        .options(
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene),
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.character),
        )
        .where(SceneChart.script_id == script_id)
    )
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="Scene chart not found")

    return await _build_scene_chart_response(chart, script, db)


# ===========================
# 手動マッピング
# ===========================


@project_router.post("/{project_id}/scene-chart/mappings", status_code=201)
async def add_manual_mapping(
    project_id: UUID,
    data: SceneCharacterMappingToggle,
    editor_member: ProjectMember = Depends(get_project_editor_dep),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """香盤表に手動マッピングを追加（セリフなし出演）."""
    script, chart = await _get_project_script_and_chart(project_id, db)

    # シーンとキャラクターがこのスクリプトに属するか確認
    scene = await _verify_scene(data.scene_id, script.id, db)
    character = await _verify_character(data.character_id, script.id, db)

    # 重複チェック
    existing = await db.execute(
        select(SceneCharacterMapping).where(
            SceneCharacterMapping.chart_id == chart.id,
            SceneCharacterMapping.scene_id == data.scene_id,
            SceneCharacterMapping.character_id == data.character_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="このマッピングは既に存在します")

    mapping = SceneCharacterMapping(
        id=uuid_mod.uuid4(),
        chart_id=chart.id,
        scene_id=data.scene_id,
        character_id=data.character_id,
        is_manual=True,
    )
    db.add(mapping)
    await db.commit()

    return {"status": "created"}


@project_router.delete("/{project_id}/scene-chart/mappings", status_code=204)
async def remove_manual_mapping(
    project_id: UUID,
    data: SceneCharacterMappingToggle,
    editor_member: ProjectMember = Depends(get_project_editor_dep),
    db: AsyncSession = Depends(get_db),
) -> None:
    """手動マッピングを削除."""
    script, chart = await _get_project_script_and_chart(project_id, db)

    result = await db.execute(
        select(SceneCharacterMapping).where(
            SceneCharacterMapping.chart_id == chart.id,
            SceneCharacterMapping.scene_id == data.scene_id,
            SceneCharacterMapping.character_id == data.character_id,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping is None:
        raise HTTPException(status_code=404, detail="マッピングが見つかりません")

    if not mapping.is_manual:
        raise HTTPException(status_code=400, detail="脚本由来のマッピングは削除できません")

    await db.delete(mapping)
    await db.commit()


# ===========================
# シーン CRUD
# ===========================


@project_router.post("/{project_id}/scenes", status_code=201)
async def create_custom_scene(
    project_id: UUID,
    data: SceneCreate,
    editor_member: ProjectMember = Depends(get_project_editor_dep),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """カスタムシーンを追加."""
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    scene = Scene(
        script_id=script.id,
        heading=data.heading,
        act_number=data.act_number,
        scene_number=data.scene_number,
        is_custom=True,
    )
    db.add(scene)
    await db.commit()

    return {
        "id": str(scene.id),
        "heading": scene.heading,
        "act_number": scene.act_number,
        "scene_number": scene.scene_number,
        "is_custom": True,
    }


@project_router.delete("/{project_id}/scenes/{scene_id}", status_code=204)
async def delete_custom_scene(
    project_id: UUID,
    scene_id: UUID,
    editor_member: ProjectMember = Depends(get_project_editor_dep),
    db: AsyncSession = Depends(get_db),
) -> None:
    """カスタムシーンを削除."""
    result = await db.execute(
        select(Scene)
        .join(Script)
        .where(Scene.id == scene_id, Script.project_id == project_id)
    )
    scene = result.scalar_one_or_none()
    if scene is None:
        raise HTTPException(status_code=404, detail="シーンが見つかりません")

    if not scene.is_custom:
        raise HTTPException(status_code=400, detail="脚本由来のシーンは削除できません")

    # 依存するマッピングを先に削除（FK違反防止）
    from sqlalchemy import delete as sa_delete

    await db.execute(
        sa_delete(SceneCharacterMapping).where(SceneCharacterMapping.scene_id == scene_id)
    )
    await db.delete(scene)
    await db.commit()


@project_router.patch("/{project_id}/scenes/{scene_id}")
async def update_scene(
    project_id: UUID,
    scene_id: UUID,
    data: SceneUpdate,
    editor_member: ProjectMember = Depends(get_project_editor_dep),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """シーンの見出し・幕番号・シーン番号を編集."""
    result = await db.execute(
        select(Scene)
        .join(Script)
        .where(Scene.id == scene_id, Script.project_id == project_id)
    )
    scene = result.scalar_one_or_none()
    if scene is None:
        raise HTTPException(status_code=404, detail="シーンが見つかりません")

    if "heading" in data.model_fields_set:
        scene.heading = data.heading
    if "act_number" in data.model_fields_set:
        scene.act_number = data.act_number
    if "scene_number" in data.model_fields_set and data.scene_number is not None:
        if data.scene_number < 1:
            raise HTTPException(status_code=400, detail="シーン番号は1以上を指定してください")
        scene.scene_number = data.scene_number

    await db.commit()

    return {
        "id": str(scene.id),
        "heading": scene.heading,
        "act_number": scene.act_number,
        "scene_number": scene.scene_number,
        "is_custom": scene.is_custom,
    }


# ===========================
# ヘルパー関数
# ===========================


async def _get_project_script_and_chart(
    project_id: UUID, db: AsyncSession
) -> tuple[Script, SceneChart]:
    """プロジェクトのScriptとSceneChartを取得."""
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    result = await db.execute(select(SceneChart).where(SceneChart.script_id == script.id))
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="香盤表が見つかりません")

    return script, chart


async def _verify_scene(scene_id: UUID, script_id: UUID, db: AsyncSession) -> Scene:
    """シーンが指定スクリプトに属するか確認."""
    result = await db.execute(
        select(Scene).where(Scene.id == scene_id, Scene.script_id == script_id)
    )
    scene = result.scalar_one_or_none()
    if scene is None:
        raise HTTPException(status_code=404, detail="シーンが見つかりません")
    return scene


async def _verify_character(character_id: UUID, script_id: UUID, db: AsyncSession) -> Character:
    """キャラクターが指定スクリプトに属するか確認."""
    result = await db.execute(
        select(Character).where(Character.id == character_id, Character.script_id == script_id)
    )
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")
    return character


async def _build_scene_chart_response(
    chart: SceneChart, script: Script, db: AsyncSession
) -> SceneChartResponse:
    """香盤表レスポンスを構築（全シーンを含む）."""
    # マッピングデータをロード
    result = await db.execute(
        select(SceneChart)
        .options(
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene),
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.character),
        )
        .where(SceneChart.id == chart.id)
    )
    chart = result.scalar_one()

    # シーンごとにマッピングをグループ化
    scene_dict: dict[UUID, SceneInChart] = {}

    for mapping in chart.mappings:
        scene_id = mapping.scene_id
        if scene_id not in scene_dict:
            scene_dict[scene_id] = SceneInChart(
                scene_id=scene_id,
                act_number=mapping.scene.act_number,
                scene_number=mapping.scene.scene_number,
                scene_heading=mapping.scene.heading,
                is_custom=mapping.scene.is_custom,
                characters=[],
            )

        scene_dict[scene_id].characters.append(
            CharacterInScene(
                id=mapping.character.id,
                name=mapping.character.name,
                order=mapping.character.order,
                is_custom=mapping.character.is_custom,
                is_manual=mapping.is_manual,
            )
        )

    # マッピングがないシーンも含める（全シーン表示）
    all_scenes_result = await db.execute(
        select(Scene).where(Scene.script_id == script.id, Scene.scene_number > 0)
    )
    all_scenes = all_scenes_result.scalars().all()

    for scene in all_scenes:
        if scene.id not in scene_dict:
            scene_dict[scene.id] = SceneInChart(
                scene_id=scene.id,
                act_number=scene.act_number,
                scene_number=scene.scene_number,
                scene_heading=scene.heading,
                is_custom=scene.is_custom,
                characters=[],
            )

    # Act と Scene の昇順でソート
    scenes = sorted(scene_dict.values(), key=lambda s: (s.act_number or 0, s.scene_number))

    return SceneChartResponse(
        id=chart.id,
        script_id=chart.script_id,
        created_at=chart.created_at,
        updated_at=chart.updated_at,
        scenes=scenes,
    )
