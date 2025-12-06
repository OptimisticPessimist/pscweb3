"""香盤表自動生成サービス."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Scene, SceneChart, SceneCharacterMapping, Script


async def generate_scene_chart(script: Script, db: AsyncSession) -> SceneChart:
    """脚本から香盤表を自動生成.

    Args:
        script: 脚本モデル
        db: データベースセッション

    Returns:
        SceneChart: 生成された香盤表
    """
    # 既存の香盤表を削除（再生成）
    result = await db.execute(
        select(SceneChart).where(SceneChart.script_id == script.id)
    )
    existing_chart = result.scalar_one_or_none()
    if existing_chart:
        await db.delete(existing_chart)
        await db.flush()

    # 新しい香盤表を作成
    chart = SceneChart(script_id=script.id)
    db.add(chart)
    await db.flush()

    # 各シーンに登場する人物を抽出してマッピング
    for scene in script.scenes:
        # このシーンに登場する人物を取得（Lineから抽出）
        character_ids = {line.character_id for line in scene.lines}

        # マッピング作成
        for character_id in character_ids:
            mapping = SceneCharacterMapping(
                chart_id=chart.id,
                scene_id=scene.id,
                character_id=character_id,
            )
            db.add(mapping)

    await db.flush()
    await db.refresh(chart)

    return chart
