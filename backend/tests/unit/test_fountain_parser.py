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
