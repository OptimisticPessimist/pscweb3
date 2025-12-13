
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services.fountain_parser import parse_fountain_and_create_models
from src.db.models import TheaterProject, User, Script, Scene, Line

@pytest.mark.asyncio
async def test_jp_fountain_features(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """日本語Fountain特有記法のパーステスト."""
    
    # 1. Forced Scene Heading (.シーン)
    # 2. Section Heading as Scene (## シーン)
    # 3. Indented Action ( Togaki)
    # 4. One-line Dialogue (@Name Dialogue)
    
    fountain_content = """Title: JP Features Test
Author: Tester

.1 第一幕（強制Act）

.2 シーン１（強制Scene）

（ここにアクション）

@ピーター 一行セリフです。

　　全角スペースインデントのト書き。

## セクションシーン（２）

@花子 (ハナコ)
通常のセリフも大丈夫？
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="JP Features Test",
        content=fountain_content,
    )
    db.add(script)
    await db.flush()
    
    # Act
    await parse_fountain_and_create_models(
        script=script,
        fountain_content=fountain_content,
        db=db
    )
    await db.commit()
    
    # Reload script with relations
    result = await db.execute(
        select(Script)
        .where(Script.id == script.id)
        .options(
            selectinload(Script.scenes).selectinload(Scene.lines).selectinload(Line.character)
        )
    )
    script_loaded = result.scalar_one()
    
    # Sort scenes by number
    scenes = sorted(script_loaded.scenes, key=lambda x: x.scene_number)
    assert len(scenes) == 2
    
    # Verify Scene 1: Forced Heading with .2
    scene1 = scenes[0]
    # .1 Act -> count=1. .2 Scene -> scene count=1.
    assert scene1.act_number == 1
    assert "シーン１" in scene1.heading
    assert not scene1.heading.startswith(".") 
    
    lines1 = sorted(scene1.lines, key=lambda x: x.order)
    assert len(lines1) == 3 
    
    # Line 1: Action
    assert "（ここにアクション）" in lines1[0].content
    assert lines1[0].character_id is None
    
    # Line 2: One-line Dialogue
    assert lines1[1].character_id is not None
    assert lines1[1].character.name == "ピーター"
    assert lines1[1].content == "一行セリフです。"
    
    # Line 3: Indented Action
    # Check if full-width space is preserved
    assert "　　全角スペースインデント" in lines1[2].content
    assert lines1[2].character_id is None
    
    # Verify Scene 2: Section Heading
    scene2 = scenes[1]
    assert "セクションシーン（２）" in scene2.heading
    assert not scene2.heading.startswith("#")
    
    lines2 = sorted(scene2.lines, key=lambda x: x.order)
    assert len(lines2) >= 1
    
    # Normal dialogue check
    normal_dialogue = lines2[0]
    assert normal_dialogue.character is not None
    assert normal_dialogue.character.name == "花子 (ハナコ)"
    assert "通常のセリフ" in normal_dialogue.content
