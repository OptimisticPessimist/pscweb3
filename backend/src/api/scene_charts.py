"""香盤表APIエンドポイント."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user_dep
from src.db import get_db
from src.db.models import ProjectMember, SceneChart, Script, User, SceneCharacterMapping
from src.schemas.scene_chart import CharacterInScene, SceneChartResponse, SceneInChart
from src.services.scene_chart_generator import generate_scene_chart
from src.dependencies.permissions import get_script_member_dep

router = APIRouter()


@router.post("/{script_id}/generate-scene-chart", response_model=SceneChartResponse)
async def create_scene_chart(
    script_id: UUID,
    member_and_script: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """脚本から香盤表を自動生成.

    Args:
        script_id: 脚本ID
        member_and_script: メンバー情報と脚本（依存関係から取得）
        db: データベースセッション

    Returns:
        SceneChartResponse: 生成された香盤表
    """
    # member_and_script は get_script_member_dep で認証・権限チェック済み
    member, script = member_and_script

    # 香盤表生成
    chart = await generate_scene_chart(script, db)
    await db.commit()
    await db.refresh(chart)

    # レスポンス整形
    return _build_scene_chart_response(chart)


@router.get("/{script_id}/scene-chart", response_model=SceneChartResponse)
async def get_scene_chart(
    script_id: UUID,
    member_and_script: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """香盤表を取得.

    Args:
        script_id: 脚本ID
        member_and_script: メンバー情報と脚本
        db: データベースセッション

    Returns:
        SceneChartResponse: 香盤表
    """
    # member_and_script は get_script_member_dep で認証・権限チェック済み
    member, script = member_and_script

    # 香盤表取得 (関連データも一括取得)
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(SceneChart)
        .options(
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene),
            selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.character)
        )
        .where(SceneChart.script_id == script_id)
    )
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="Scene chart not found")

    # レスポンス整形
    return _build_scene_chart_response(chart)


def _build_scene_chart_response(chart: SceneChart) -> SceneChartResponse:
    """香盤表レスポンスを構築.

    Args:
        chart: 香盤表モデル

    Returns:
        SceneChartResponse: 整形されたレスポンス
    """
    # シーンごとにグループ化
    scene_dict: dict[UUID, SceneInChart] = {}

    for mapping in chart.mappings:
        scene_id = mapping.scene_id
        if scene_id not in scene_dict:
            scene_dict[scene_id] = SceneInChart(
                act_number=mapping.scene.act_number,
                scene_number=mapping.scene.scene_number,
                scene_heading=mapping.scene.heading,
                characters=[],
            )

        scene_dict[scene_id].characters.append(
            CharacterInScene(
                id=mapping.character.id,
                name=mapping.character.name,
            )
        )

    # シーン番号順にソート
    scenes = sorted(scene_dict.values(), key=lambda s: s.scene_number)

    return SceneChartResponse(
        id=chart.id,
        script_id=chart.script_id,
        created_at=chart.created_at,
        updated_at=chart.updated_at,
        scenes=scenes,
    )
