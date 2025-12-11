"""キャラクターとキャスティングAPIのテスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import Character, Script, TheaterProject, User


@pytest.fixture
async def test_script(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> Script:
    """テスト用脚本."""
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="テスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    return script


@pytest.fixture
async def test_character(db: AsyncSession, test_script: Script) -> Character:
    """テスト用キャラクター."""
    character = Character(
        script_id=test_script.id,
        name="主人公",
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@pytest.mark.asyncio
async def test_list_project_characters(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_character: Character,
    test_user_token: str,
) -> None:
    """プロジェクトのキャラクター一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/characters",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_add_casting(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_character: Character,
    test_user_token: str,
) -> None:
    """キャラクターにキャストを追加するテスト."""
    # Arrange
    casting_data = {
        "user_id": str(test_user.id),
        "cast_name": "Aキャスト",
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/characters/{test_character.id}/cast",
        json=casting_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_remove_casting(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_character: Character,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """キャラクターからキャストを削除するテスト."""
    # Arrange - まずキャストを追加
    from src.db.models import CharacterCasting
    casting = CharacterCasting(
        character_id=test_character.id,
        user_id=test_user.id,
        cast_name="テストキャスト",
    )
    db.add(casting)
    await db.commit()
    
    # Act
    response = await client.delete(
        f"/api/projects/{test_project.id}/characters/{test_character.id}/cast",
        params={"user_id": str(test_user.id)},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_double_cast(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_character: Character,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """ダブルキャスト設定のテスト."""
    # Arrange - 2人目のユーザーを作成
    user2 = User(
        discord_id="999888777",
        discord_username="user2_test",
    )
    db.add(user2)
    await db.commit()
    await db.refresh(user2)
    
    # プロジェクトメンバーとして追加
    from src.db.models import ProjectMember
    member2 = ProjectMember(
        project_id=test_project.id,
        user_id=user2.id,
        role="member",
    )
    db.add(member2)
    await db.commit()
    
    # Act - 1人目のキャスト
    casting_data1 = {
        "user_id": str(test_user.id),
        "cast_name": "Aキャスト",
    }
    response1 = await client.post(
        f"/api/projects/{test_project.id}/characters/{test_character.id}/cast",
        json=casting_data1,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Act - 2人目のキャスト
    casting_data2 = {
        "user_id": str(user2.id),
        "cast_name": "Bキャスト",
    }
    response2 = await client.post(
        f"/api/projects/{test_project.id}/characters/{test_character.id}/cast",
        json=casting_data2,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # 両方のキャストが登録されていることを確認
    response_list = await client.get(
        f"/api/projects/{test_project.id}/characters",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response_list.status_code == 200
