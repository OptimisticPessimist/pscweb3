"""稽古API詳細テスト（参加者管理・キャスト管理）."""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Rehearsal, RehearsalSchedule, TheaterProject, User, ProjectMember, Character, Script


@pytest.fixture
async def test_character(db: AsyncSession, test_project: TheaterProject, test_user: User) -> Character:
    """テスト用キャラクター（稽古用）."""
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="稽古テスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.flush()
    
    character = Character(
        script_id=script.id,
        name="テストキャラクター",
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@pytest.mark.asyncio
async def test_add_rehearsal_participant(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """稽古参加者追加のテスト."""
    # Act
    response = await client.post(
        f"/api/rehearsals/{test_rehearsal.id}/participants/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_participant_role(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """参加者の役割更新のテスト."""
    # Arrange - まず参加者として追加
    await client.post(
        f"/api/rehearsals/{test_rehearsal.id}/participants/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    role_update = {
        "staff_role": "director",
    }
    
    # Act
    response = await client.put(
        f"/api/rehearsals/{test_rehearsal.id}/participants/{test_user.id}",
        json=role_update,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_participant(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """参加者削除のテスト."""
    # Arrange
    await client.post(
        f"/api/rehearsals/{test_rehearsal.id}/participants/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Act
    response = await client.delete(
        f"/api/rehearsals/{test_rehearsal.id}/participants/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_rehearsal_cast(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_character: Character,
    test_user_token: str,
) -> None:
    """稽古キャスト追加のテスト."""
    # Arrange
    cast_data = {
        "character_id": str(test_character.id),
        "user_id": str(test_user.id),
    }
    
    # Act
    response = await client.post(
        f"/api/rehearsals/{test_rehearsal.id}/casts",
        json=cast_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_rehearsal_cast(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_character: Character,
    test_user_token: str,
) -> None:
    """稽古キャスト削除のテスト."""
    # Arrange - まずキャストを追加
    cast_data = {
        "character_id": str(test_character.id),
        "user_id": str(test_user.id),
    }
    await client.post(
        f"/api/rehearsals/{test_rehearsal.id}/casts",
        json=cast_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Act
    response = await client.delete(
        f"/api/rehearsals/{test_rehearsal.id}/casts/{test_character.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_rehearsal_with_participants(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_rehearsal_schedule: RehearsalSchedule,
    test_user_token: str,
) -> None:
    """参加者指定での稽古作成のテスト."""
    # Arrange
    rehearsal_data = {
        "date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
        "duration_minutes": 120,
        "location": "稽古場",
        "notes": "通し稽古",
        "participants": [
            {
                "user_id": str(test_user.id),
                "staff_role": "director"
            }
        ],
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/rehearsals",
        json=rehearsal_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_update_rehearsal_with_casts(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_character: Character,
    test_user_token: str,
) -> None:
    """キャスト指定での稽古更新のテスト."""
    # Arrange
    update_data = {
        "notes": "更新された稽古",
        "casts": [
            {
                "character_id": str(test_character.id),
                "user_id": str(test_user.id)
            }
        ],
    }
    
    # Act
    response = await client.put(
        f"/api/rehearsals/{test_rehearsal.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
