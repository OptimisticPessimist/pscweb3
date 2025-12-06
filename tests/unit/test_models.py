"""データベースモデルのテスト."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Character,
    CharacterCasting,
    Line,
    Scene,
    Script,
    TheaterProject,
    User,
)


@pytest.mark.asyncio
async def test_create_user(db: AsyncSession) -> None:
    """ユーザー作成のテスト.

    AAAパターンに従ったテスト例。
    """
    # Arrange: テストデータを準備
    discord_id = "987654321"
    discord_username = "newuser"

    # Act: ユーザーを作成
    user = User(
        discord_id=discord_id,
        discord_username=discord_username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Assert: 結果を検証
    assert user.id is not None
    assert user.discord_id == discord_id
    assert user.discord_username == discord_username
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_project(db: AsyncSession, test_user: User) -> None:
    """プロジェクト作成のテスト."""
    # Arrange
    project_name = "新しい舞台"
    project_description = "テスト用の説明"

    # Act
    project = TheaterProject(
        name=project_name,
        description=project_description,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Assert
    assert project.id is not None
    assert project.name == project_name
    assert project.description == project_description
    assert project.created_at is not None


@pytest.mark.asyncio
async def test_create_script_with_scenes_and_characters(
    db: AsyncSession, test_project: TheaterProject
) -> None:
    """脚本、シーン、登場人物の作成テスト."""
    # Arrange
    script_title = "ハムレット"
    blob_path = "scripts/1/hamlet.fountain"

    # Act: 脚本作成
    script = Script(
        project_id=test_project.id,
        title=script_title,
        blob_path=blob_path,
    )
    db.add(script)
    await db.flush()

    # シーン作成
    scene = Scene(
        script_id=script.id,
        scene_number=1,
        heading="INT. ELSINORE CASTLE - DAY",
        description="城の中",
    )
    db.add(scene)
    await db.flush()

    # 登場人物作成
    character = Character(
        script_id=script.id,
        name="ハムレット",
    )
    db.add(character)
    await db.flush()

    # セリフ作成
    line = Line(
        scene_id=scene.id,
        character_id=character.id,
        content="生きるべきか死ぬべきか、それが問題だ",
        order=1,
    )
    db.add(line)

    await db.commit()
    await db.refresh(script)

    # Assert
    assert script.id is not None
    assert script.title == script_title
    assert len(script.scenes) == 1
    assert len(script.characters) == 1
    assert script.scenes[0].heading == "INT. ELSINORE CASTLE - DAY"
    assert script.characters[0].name == "ハムレット"


@pytest.mark.asyncio
async def test_character_casting_double_cast(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> None:
    """ダブルキャストのテスト."""
    # Arrange: 脚本と登場人物を作成
    script = Script(
        project_id=test_project.id,
        title="テスト脚本",
        blob_path="scripts/1/test.fountain",
    )
    db.add(script)
    await db.flush()

    character = Character(
        script_id=script.id,
        name="主人公",
    )
    db.add(character)
    await db.flush()

    # ユーザー2を作成
    user2 = User(
        discord_id="111222333",
        discord_username="user2",
    )
    db.add(user2)
    await db.flush()

    # Act: ダブルキャスト設定
    casting1 = CharacterCasting(
        character_id=character.id,
        user_id=test_user.id,
        cast_name="Aキャスト",
    )
    casting2 = CharacterCasting(
        character_id=character.id,
        user_id=user2.id,
        cast_name="Bキャスト",
    )
    db.add(casting1)
    db.add(casting2)
    await db.commit()
    await db.refresh(character)

    # Assert: 同じ役に2人のユーザーが割り当てられている
    assert len(character.castings) == 2
    assert character.castings[0].cast_name == "Aキャスト"
    assert character.castings[1].cast_name == "Bキャスト"
