
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services.fountain_parser import parse_fountain_and_create_models
from src.db.models import TheaterProject, User, Script, Scene, Line

@pytest.mark.asyncio
async def test_preserve_synopsis_and_parenthetical(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """あらすじ(=)や括弧書き、移行が正しく保存されることを確認."""
    # Arrange
    fountain_content = """Title: Preservation Test

# あらすじ
= 1行目のあらすじ
= 2行目のあらすじ

## シーン1
通常ト書き

BRICK
(whispering)
Hello.

> CUT TO:
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Preservation Test",
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
    
    # Assert
    result = await db.execute(
        select(Script)
        .where(Script.id == script.id)
        .options(selectinload(Script.scenes).selectinload(Scene.lines))
    )
    script_loaded = result.scalar_one()
    scenes = sorted(script_loaded.scenes, key=lambda x: x.scene_number)
    
    assert len(scenes) == 2 # Synopsis(0) and Scene 1
    
    # Check Synopsis (Scene 0)
    synopsis_scene = scenes[0]
    synopsis_lines = sorted(synopsis_scene.lines, key=lambda x: x.order)
    
    # 私の実装では、= を除いた内容が保存されるはず
    assert any("1行目のあらすじ" in line.content for line in synopsis_lines)
    assert any("2行目のあらすじ" in line.content for line in synopsis_lines)
    
    # Scene 1
    scene1 = scenes[1]
    scene1_lines = sorted(scene1.lines, key=lambda x: x.order)
    
    # Check Parenthetical (should be associated with BRICK if implemented that way)
    parenthetical_line = next((line for line in scene1_lines if "(whispering)" in line.content), None)
    assert parenthetical_line is not None
    assert parenthetical_line.character_id is not None # Associated with BRICK
    
    # Check Transition
    transition_line = next((line for line in scene1_lines if "CUT TO:" in line.content), None)
    assert transition_line is not None
    
    # Check Scene Description (accumulated)
    # 最初のActionまたはSynopsisが収集される設定
    assert "1行目のあらすじ" in synopsis_scene.description
    assert "2行目のあらすじ" in synopsis_scene.description
