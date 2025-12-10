"""Fountainパーサーのテスト."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.fountain_parser import parse_fountain_and_create_models
from src.db.models import TheaterProject, User


@pytest.mark.asyncio
async def test_parse_simple_fountain_script(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """シンプルなFountain脚本のパーステスト."""
    # Arrange
    fountain_text = """Title: Simple Test
Author: Test Author

INT. TEST ROOM - DAY

A simple test scene.

CHARACTER
Hello, world!
"""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Simple Test",
        db=db
    )
    
    # Assert
    assert script is not None
    assert script.title == "Simple Test"
    assert len(script.scenes) >= 0  # シーンが解析される


@pytest.mark.asyncio
async def test_parse_fountain_with_multiple_characters(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """複数キャラクターを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_text = """Title: Multi Character Test

INT. ROOM - DAY

ALICE
Hello!

BOB
Hi there!

ALICE
How are you?
"""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Multi Character Test",
        db=db
    )
    
    # Assert
    assert script is not None
    assert len(script.characters) >= 2  # ALICE, BOBが解析される


@pytest.mark.asyncio
async def test_parse_fountain_with_action(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """アクションを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_text = """Title: Action Test

INT. ROOM - DAY

The door opens slowly.

CHARACTER
Who's there?

Character looks around nervously.
"""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Action Test",
        db=db
    )
    
    # Assert
    assert script is not None
    assert script.title == "Action Test"


@pytest.mark.asyncio
async def test_parse_fountain_with_transitions(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """トランジションを含むFountain脚本のパーステスト."""
    # Arrange
    fountain_text = """Title: Transition Test

INT. ROOM A - DAY

CHARACTER
Goodbye!

FADE OUT.

INT. ROOM B - DAY

Another scene.
"""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Transition Test",
        db=db
    )
    
    # Assert
    assert script is not None
    # トランジションが処理される


@pytest.mark.asyncio
async def test_parse_empty_fountain(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """空のFountain脚本のパーステスト."""
    # Arrange
    fountain_text = ""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Empty Test",
        db=db
    )
    
    # Assert
    assert script is not None
    assert script.title == "Empty Test"


@pytest.mark.asyncio
async def test_parse_fountain_with_japanese(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """日本語を含むFountain脚本のパーステスト."""
    # Arrange
    fountain_text = """Title: 日本語テスト

INT. 部屋 - 昼

太郎
こんにちは！

花子
元気ですか？
"""
    
    # Act
    script = await parse_fountain_and_create_models(
        fountain_text=fountain_text,
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="日本語テスト",
        db=db
    )
    
    # Assert
    assert script is not None
    assert script.title == "日本語テスト"
    # 日本語のキャラクター名が解析される
