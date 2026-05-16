"""香盤表自動生成サービス."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SceneCharacterMapping, SceneChart, Script


async def generate_scene_chart(script: Script, db: AsyncSession) -> SceneChart:
    """脚本から香盤表を自動生成.

    手動マッピング（is_manual=True）は保持し、自動マッピングのみ再生成する。
    SceneChart自体が存在しない場合は新規作成する。

    Args:
        script: 脚本モデル
        db: データベースセッション

    Returns:
        SceneChart: 生成された香盤表
    """
    # 既存の香盤表を確認
    result = await db.execute(select(SceneChart).where(SceneChart.script_id == script.id))
    existing_chart = result.scalar_one_or_none()

    if existing_chart:
        # 自動マッピングのみ削除（手動マッピングは保持）
        await db.execute(
            SceneCharacterMapping.__table__.delete().where(
                SceneCharacterMapping.chart_id == existing_chart.id,
                SceneCharacterMapping.is_manual == False,  # noqa: E712
            )
        )
        await db.flush()
        chart = existing_chart
    else:
        # 新しい香盤表を作成
        chart = SceneChart(id=uuid.uuid4(), script_id=script.id)
        db.add(chart)
        await db.flush()

    # 手動マッピングのキーセットを取得（重複防止）
    manual_result = await db.execute(
        select(SceneCharacterMapping.scene_id, SceneCharacterMapping.character_id).where(
            SceneCharacterMapping.chart_id == chart.id,
            SceneCharacterMapping.is_manual == True,  # noqa: E712
        )
    )
    manual_keys = {(row.scene_id, row.character_id) for row in manual_result.all()}

    # 各シーンに登場する人物を抽出してマッピング（脚本由来のシーンのみ）
    for scene in script.scenes:
        # カスタムシーンおよびシーン番号が0以下のもの（あらすじなど）はスキップ
        if scene.is_custom or scene.scene_number <= 0:
            continue

        # このシーンに登場する人物を取得（Lineから抽出）
        character_ids = {line.character_id for line in scene.lines if line.character_id is not None}

        # マッピング作成（手動マッピングと重複しないもののみ）
        for character_id in character_ids:
            if (scene.id, character_id) not in manual_keys:
                mapping = SceneCharacterMapping(
                    id=uuid.uuid4(),
                    chart_id=chart.id,
                    scene_id=scene.id,
                    character_id=character_id,
                    is_manual=False,
                )
                db.add(mapping)

    await db.flush()
    await db.refresh(chart)

    return chart


async def ensure_scene_chart(script: Script, db: AsyncSession) -> SceneChart:
    """香盤表が存在しなければ空で作成する.

    Args:
        script: 脚本モデル
        db: データベースセッション

    Returns:
        SceneChart: 既存または新規の香盤表
    """
    result = await db.execute(select(SceneChart).where(SceneChart.script_id == script.id))
    chart = result.scalar_one_or_none()

    if chart is None:
        chart = SceneChart(id=uuid.uuid4(), script_id=script.id)
        db.add(chart)
        await db.flush()

    return chart
