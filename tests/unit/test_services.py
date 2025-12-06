"""Fountainパーサーサービスのテスト."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Script, TheaterProject
from src.services.fountain_parser import parse_fountain_and_create_models


@pytest.mark.asyncio
async def test_parse_simple_fountain_script(
    db: AsyncSession, test_project: TheaterProject
) -> None:
    """シンプルなFountain脚本のパーステスト."""
    # Arrange: Fountain形式の脚本
    fountain_content = """Title: テスト脚本

INT. テスト部屋 - DAY

少年と少女が会話している。

少年
こんにちは。

少女
こんにちは、元気？

少年
うん、元気だよ。
"""

    script = Script(
        project_id=test_project.id,
        title="テスト脚本",
        blob_path="test.fountain",
    )
    db.add(script)
    await db.flush()

    # Act: Fountainパース
    await parse_fountain_and_create_models(script, fountain_content, db)
    await db.commit()
    await db.refresh(script)

    # Assert: シーン、登場人物、セリフが作成されている
    assert len(script.scenes) >= 1, "少なくとも1つのシーンが作成されるはず"
    assert len(script.characters) == 2, "2人の登場人物が作成されるはず"

    # 登場人物名を確認
    character_names = {char.name for char in script.characters}
    assert "少年" in character_names
    assert "少女" in character_names


@pytest.mark.asyncio
async def test_parse_fountain_with_multiple_scenes(
    db: AsyncSession, test_project: TheaterProject
) -> None:
    """複数シーンを持つFountain脚本のパーステスト."""
    # Arrange
    fountain_content = """Title: マルチシーン脚本

INT. リビング - DAY

母
ご飯できたわよ。

EXT. 公園 - DAY

子供たち
わーい！
"""

    script = Script(
        project_id=test_project.id,
        title="マルチシーン脚本",
        blob_path="multi.fountain",
    )
    db.add(script)
    await db.flush()

    # Act
    await parse_fountain_and_create_models(script, fountain_content, db)
    await db.commit()
    await db.refresh(script)

    # Assert: 2つのシーンが作成されている
    assert len(script.scenes) >= 2, "2つのシーンが作成されるはず"


@pytest.mark.asyncio
async def test_parse_fountain_empty_script(
    db: AsyncSession, test_project: TheaterProject
) -> None:
    """空のFountain脚本のパーステスト."""
    # Arrange
    fountain_content = "Title: 空の脚本"

    script = Script(
        project_id=test_project.id,
        title="空の脚本",
        blob_path="empty.fountain",
    )
    db.add(script)
    await db.flush()

    # Act
    await parse_fountain_and_create_models(script, fountain_content, db)
    await db.commit()
    await db.refresh(script)

    # Assert: シーンも登場人物もない
    assert len(script.scenes) == 0
    assert len(script.characters) == 0
