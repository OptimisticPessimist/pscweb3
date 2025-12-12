"""Fountainパーサーのテスト."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.fountain_parser import parse_fountain_and_create_models
from src.db.models import TheaterProject, User, Script


@pytest.mark.asyncio
async def test_parse_simple_fountain_script(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """シンプルなFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Simple Test
Author: Test Author

INT. TEST ROOM - DAY

A simple test scene.

CHARACTER
Hello, world!
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Simple Test",
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
    assert script is not None
    assert script.title == "Simple Test"


@pytest.mark.asyncio
async def test_parse_fountain_with_multiple_characters(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """複数キャラクターを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Multi Character Test

INT. ROOM - DAY

ALICE
Hello!

BOB
Hi there!

ALICE
How are you?
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Multi Character Test",
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
    assert script is not None


@pytest.mark.asyncio
async def test_parse_fountain_with_action(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """アクションを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Action Test

INT. ROOM - DAY

The door opens slowly.

CHARACTER
Who's there?

Character looks around nervously.
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Action Test",
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
    assert script is not None
    assert script.title == "Action Test"


@pytest.mark.asyncio
async def test_parse_fountain_with_transitions(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """トランジションを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Transition Test

INT. ROOM A - DAY

CHARACTER
Goodbye!

FADE OUT.

INT. ROOM B - DAY

Another scene.
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Transition Test",
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
    assert script is not None


@pytest.mark.asyncio
async def test_parse_empty_fountain(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """空のFountain脚本のパーステスト."""
    # Arrange
    fountain_content = ""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Empty Test",
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
    assert script is not None
    assert script.title == "Empty Test"


@pytest.mark.asyncio
async def test_parse_fountain_with_japanese(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """日本語を含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: 日本語テスト

INT. 部屋 - 昼

太郎
こんにちは！

花子
元気ですか？
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="日本語テスト",
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
    assert script is not None
    assert script.title == "日本語テスト"


@pytest.mark.asyncio
async def test_parse_fountain_with_action_togaki(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """ト書き（Action）を含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Action Togaki Test

INT. ROOM - DAY

Action line here (Togaki).

CHARACTER
Dialogue line.

Another action line.
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Action Togaki Test",
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
    # Reload script with lines
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Script)
        .where(Script.id == script.id)
        .options(selectinload(Script.scenes).selectinload(Scene.lines))
    )
    script_loaded = result.scalar_one()
    
    assert len(script_loaded.scenes) == 1
    lines = sorted(script_loaded.scenes[0].lines, key=lambda x: x.order)
    assert len(lines) == 3
    
    # 1. Action
    assert lines[0].content == "Action line here (Togaki)."
    assert lines[0].character_id is None
    
    # 2. Dialogue
    assert lines[1].content == "Dialogue line."
    assert lines[1].character_id is not None
    
    # 3. Action
    assert lines[2].content == "Another action line."
    assert lines[2].character_id is None


@pytest.mark.asyncio
async def test_parse_fountain_with_character_description(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """登場人物の紹介文を含むFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: Character Description Test

# 登場人物

TARO: 主人公。元気な男の子。
HANAKO: ヒロイン。

# Characters

JIRO: 太郎の弟。

INT. ROOM - DAY

TARO
Hello!
"""
    
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Character Description Test",
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
    # Reload characters
    from sqlalchemy import select
    from src.db.models import Character
    
    result = await db.execute(
        select(Character).where(Character.script_id == script.id)
    )
    characters = result.scalars().all()
    char_map = {c.name: c for c in characters}
    
    assert "TARO" in char_map
    assert char_map["TARO"].description == "主人公。元気な男の子。"
    
    assert "HANAKO" in char_map
    assert char_map["HANAKO"].description == "ヒロイン。"

    assert "JIRO" in char_map
    assert char_map["JIRO"].description == "太郎の弟。"

