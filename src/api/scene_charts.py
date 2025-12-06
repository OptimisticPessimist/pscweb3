"""香盤表APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import ProjectMember, SceneChart, Script
from src.schemas.scene_chart import CharacterInScene, SceneChartResponse, SceneInChart
from src.services.scene_chart_generator import generate_scene_chart

router = APIRouter()


@router.post("/{script_id}/generate-scene-chart", response_model=SceneChartResponse)
async def create_scene_chart(
    script_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """脚本から香盤表を自動生成.

    Args:
        script_id: 脚本ID
        token: JWT トークン
        db: データベースセッション

    Returns:
        SceneChartResponse: 生成された香盤表

    Raises:
        HTTPException: 認証エラー、権限エラー、または脚本が見つからない
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # 香盤表生成
    chart = await generate_scene_chart(script, db)
    await db.commit()
    await db.refresh(chart)

    # レスポンス整形
    return _build_scene_chart_response(chart)


@router.get("/{script_id}/scene-chart", response_model=SceneChartResponse)
async def get_scene_chart(
    script_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> SceneChartResponse:
    """香盤表を取得.

    Args:
        script_id: 脚本ID
        token: JWT トークン
        db: データベースセッション

    Returns:
        SceneChartResponse: 香盤表

    Raises:
        HTTPException: 認証エラー、権限エラー、または香盤表が見つからない
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # 香盤表取得
    result = await db.execute(
        select(SceneChart).where(SceneChart.script_id == script_id)
    )
    chart = result.scalar_one_or_none()
    if chart is None:
        raise HTTPException(status_code=404, detail="香盤表が見つかりません")

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
    scene_dict: dict[int, SceneInChart] = {}

    for mapping in chart.mappings:
        scene_id = mapping.scene_id
        if scene_id not in scene_dict:
            scene_dict[scene_id] = SceneInChart(
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
