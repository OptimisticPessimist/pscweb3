"""香盤表生成サービスのテスト."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Character, Line, Scene, Script, TheaterProject, User
from src.services.scene_chart_generator import generate_scene_chart


@pytest.mark.asyncio
async def test_generate_scene_chart_single_scene(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """1シーンの香盤表生成テスト."""
    # Arrange: 脚本とシーン、登場人物、セリフを作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="テスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.flush()

    scene = Scene(
        script_id=script.id,
        scene_number=1,
        heading="INT. テスト部屋 - DAY",
    )
    db.add(scene)
    await db.flush()

    char1 = Character(script_id=script.id, name="太郎")
    char2 = Character(script_id=script.id, name="花子")
    db.add_all([char1, char2])
    await db.flush()

    line1 = Line(
        scene_id=scene.id, character_id=char1.id, content="こんにちは", order=1
    )
    line2 = Line(
        scene_id=scene.id, character_id=char2.id, content="こんにちは", order=2
    )
    db.add_all([line1, line2])
    await db.commit()
    
    # リレーションを含めて再取得
    stmt = select(Script).options(
        selectinload(Script.scenes).selectinload(Scene.lines),
        selectinload(Script.characters)
    ).where(Script.id == script.id)
    result = await db.execute(stmt)
    script = result.scalar_one()

    # Act: 香盤表を生成
    chart = await generate_scene_chart(script, db)
    await db.commit()
    await db.refresh(chart, ["mappings"])

    # Assert: 香盤表が正しく生成されている
    assert chart.id is not None
    assert chart.script_id == script.id
    assert len(chart.mappings) == 2  # 2人の登場人物

    # マッピングの内容を確認
    character_ids = {m.character_id for m in chart.mappings}
    assert char1.id in character_ids
    assert char2.id in character_ids


@pytest.mark.asyncio
async def test_generate_scene_chart_multiple_scenes(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """複数シーンの香盤表生成テスト."""
    # Arrange
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="複数シーン脚本",
        content="",
    )
    db.add(script)
    await db.flush()

    # シーン1
    scene1 = Scene(script_id=script.id, scene_number=1, heading="INT. 部屋 - DAY")
    scene2 = Scene(script_id=script.id, scene_number=2, heading="EXT. 公園 - DAY")
    db.add_all([scene1, scene2])
    await db.flush()

    # 登場人物
    char1 = Character(script_id=script.id, name="太郎")
    char2 = Character(script_id=script.id, name="花子")
    char3 = Character(script_id=script.id, name="次郎")
    db.add_all([char1, char2, char3])
    await db.flush()

    # シーン1: 太郎と花子
    line1 = Line(scene_id=scene1.id, character_id=char1.id, content="A", order=1)
    line2 = Line(scene_id=scene1.id, character_id=char2.id, content="B", order=2)
    # シーン2: 花子と次郎
    line3 = Line(scene_id=scene2.id, character_id=char2.id, content="C", order=1)
    line4 = Line(scene_id=scene2.id, character_id=char3.id, content="D", order=2)
    db.add_all([line1, line2, line3, line4])
    await db.commit()
    
    # リレーションを含めて再取得
    stmt = select(Script).options(
        selectinload(Script.scenes).selectinload(Scene.lines),
        selectinload(Script.characters)
    ).where(Script.id == script.id)
    result = await db.execute(stmt)
    script = result.scalar_one()

    # Act
    chart = await generate_scene_chart(script, db)
    await db.commit()
    await db.refresh(chart, ["mappings"])

    # Assert
    assert chart.id is not None
    assert len(chart.mappings) == 4  # シーン1(2) + シーン2(2)

    # シーン1のマッピングを確認
    scene1_mappings = [m for m in chart.mappings if m.scene_id == scene1.id]
    assert len(scene1_mappings) == 2
    scene1_char_ids = {m.character_id for m in scene1_mappings}
    assert char1.id in scene1_char_ids
    assert char2.id in scene1_char_ids

    # シーン2のマッピングを確認
    scene2_mappings = [m for m in chart.mappings if m.scene_id == scene2.id]
    assert len(scene2_mappings) == 2
    scene2_char_ids = {m.character_id for m in scene2_mappings}
    assert char2.id in scene2_char_ids
    assert char3.id in scene2_char_ids


@pytest.mark.asyncio
async def test_regenerate_scene_chart(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """香盤表の再生成テスト（既存を削除して新規作成）."""
    # Arrange
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="再生成テスト",
        content=""
    )
    db.add(script)
    await db.flush()

    scene = Scene(script_id=script.id, scene_number=1, heading="INT. ROOM - DAY")
    db.add(scene)
    await db.flush()

    char = Character(script_id=script.id, name="太郎")
    db.add(char)
    await db.flush()

    line = Line(scene_id=scene.id, character_id=char.id, content="テスト", order=1)
    db.add(line)
    await db.commit()
    
    # リレーションを含めて再取得
    stmt = select(Script).options(
        selectinload(Script.scenes).selectinload(Scene.lines),
        selectinload(Script.characters)
    ).where(Script.id == script.id)
    result = await db.execute(stmt)
    script = result.scalar_one()

    # 最初の生成
    chart1 = await generate_scene_chart(script, db)
    await db.commit()
    chart1_id = chart1.id

    # Act: 再生成
    chart2 = await generate_scene_chart(script, db)
    await db.commit()

    # Assert: 新しい香盤表が作成されている
    assert chart2.id is not None
    assert chart2.script_id == script.id
