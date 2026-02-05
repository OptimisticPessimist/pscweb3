
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services.fountain_parser import parse_fountain_and_create_models
from src.services.scene_chart_generator import generate_scene_chart
from src.db.models import TheaterProject, User, Script, Scene, SceneChart

@pytest.mark.asyncio
async def test_parse_synopsis_as_scene_0(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """あらすじがシーン0としてパースされることを確認."""
    # Arrange
    fountain_content = """Title: Synopsis Test

# あらすじ
ここで物語の全体像が説明される。

.1 第1幕
Act 1 start.

## シーン1
Real Scene 1.

.2 シーン2
Real Scene 2.
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Synopsis Test",
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
    # Reload script with scenes
    result = await db.execute(
        select(Script)
        .where(Script.id == script.id)
        .options(selectinload(Script.scenes))
    )
    script_loaded = result.scalar_one()
    
    # Sort scenes by scene_number
    scenes = sorted(script_loaded.scenes, key=lambda x: x.scene_number)
    
    # We expect 3 scenes: Synopsis (0), Scene 1 (1), Scene 2 (2)
    assert len(scenes) == 3
    
    # Check Synopsis
    assert scenes[0].scene_number == 0
    assert "あらすじ" in scenes[0].heading

@pytest.mark.asyncio
async def test_parse_synopsis_i18n(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """多言語のあらすじキーワードが正しくシーン0として扱われることを確認."""
    i18n_samples = [
        ("# 줄거리\n내용", "줄거리"),
        ("# 梗概\n内容", "梗概"),
        ("## Synopsis\nContent", "Synopsis"),
    ]
    
    for content, keyword in i18n_samples:
        fountain_content = f"Title: i18n Test\n\n{content}\n\n## Scene 1\nScene content."
        
        script = Script(
            project_id=test_project.id,
            uploaded_by=test_user.id,
            title=f"i18n {keyword} Test",
            content=fountain_content,
        )
        db.add(script)
        await db.flush()
        
        await parse_fountain_and_create_models(script=script, fountain_content=fountain_content, db=db)
        await db.commit()
        
        result = await db.execute(select(Script).where(Script.id == script.id).options(selectinload(Script.scenes)))
        script_loaded = result.scalar_one()
        scenes = sorted(script_loaded.scenes, key=lambda x: x.scene_number)
        
        assert scenes[0].scene_number == 0
        assert keyword in scenes[0].heading
        assert scenes[1].scene_number == 1
        assert "Scene 1" in scenes[1].heading

    

@pytest.mark.asyncio
async def test_generate_scene_chart_skips_synopsis(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """香盤表生成時にシーン0（あらすじ）がスキップされることを確認."""
    # Arrange
    # Create scenes manually or via parser
    # Using parser to be consistent with previous test
    fountain_content = """Title: Chart Test

# あらすじ
Synopsis content.

## シーン1
Scene 1 content.
"""
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Chart Test",
        content=fountain_content,
    )
    db.add(script)
    await db.flush()
    
    await parse_fountain_and_create_models(script=script, fountain_content=fountain_content, db=db)
    await db.commit()
    
    # Reload script for generator (needs scenes relation loaded?) 
    # generate_scene_chart accesses script.scenes. logic there relies on lazy loading or pre-loading.
    # The function signature is `generate_scene_chart(script: Script, db: AsyncSession)`
    # It iterates `script.scenes`. If it's not loaded, it might trigger lazy load if configured, or fail if async.
    # Ideally should pass loaded script or ensure session is active.
    
    # Let's ensure script is loaded with scenes
    result = await db.execute(
        select(Script)
        .where(Script.id == script.id)
        .options(selectinload(Script.scenes).selectinload(Scene.lines)) 
    )
    script_loaded = result.scalar_one()

    # Act
    chart = await generate_scene_chart(script_loaded, db)
    await db.commit()
    
    # Assert
    # Reload chart with mappings
    from src.db.models import SceneCharacterMapping
    result = await db.execute(
        select(SceneChart)
        .where(SceneChart.id == chart.id)
        .options(selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene))
    )
    chart_loaded = result.scalar_one()
    
    # Should only contain Scene 1
    assert len(chart_loaded.mappings) == 0 # Since no characters in Scene 1
    
    # Let's check logic:
    # generate_scene_chart logic:
    # for scene in script.scenes:
    #    if scene.scene_number <= 0: continue
    #    character_ids = ...
    #    for char_id in character_ids:
    #       add mapping
    
    # Since my scene 1 has no characters, mappings will be empty anyway.
    # I should add a character to Synopsis and Scene 1 to verify.
    
    # Re-Arrange with characters
    fountain_content_with_char = """Title: Chart Test Char

# あらすじ
Synopsis content.

@SYNOPSIS_CHAR
Hello.

## シーン1
Scene 1 content.

@SCENE_CHAR
Hi.
"""
    script2 = Script(project_id=test_project.id, uploaded_by=test_user.id, title="Chart Test 2", content=fountain_content_with_char)
    db.add(script2)
    await db.flush()
    await parse_fountain_and_create_models(script=script2, fountain_content=fountain_content_with_char, db=db)
    await db.commit()

    result = await db.execute(select(Script).where(Script.id == script2.id).options(selectinload(Script.scenes).selectinload(Scene.lines)))
    script2_loaded = result.scalar_one()
    
    # Act
    chart2 = await generate_scene_chart(script2_loaded, db)
    await db.commit()
    
    result = await db.execute(select(SceneChart).where(SceneChart.id == chart2.id).options(selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene)))
    chart2_loaded = result.scalar_one()
    
    # Synopsis has a character, Scene 1 has a character.
    # Synopsis should be skipped.
    
    # Collect Scene IDs in chart
    scene_ids_in_chart = {m.scene.id for m in chart2_loaded.mappings}
    scene_numbers_in_chart = {m.scene.scene_number for m in chart2_loaded.mappings}
    
    assert 0 not in scene_numbers_in_chart
    assert 1 in scene_numbers_in_chart
