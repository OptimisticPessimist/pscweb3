"""稽古スケジュールAPIのテスト."""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Rehearsal, RehearsalSchedule, ProjectMember, TheaterProject, User


@pytest.fixture
async def test_rehearsal_schedule(
    db: AsyncSession, test_project: TheaterProject
) -> RehearsalSchedule:
    """テスト用稽古スケジュール."""
    schedule = RehearsalSchedule(
        project_id=test_project.id,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@pytest.fixture
async def test_rehearsal(
    db: AsyncSession, test_rehearsal_schedule: RehearsalSchedule
) -> Rehearsal:
    """テスト用稽古."""
    rehearsal = Rehearsal(
        schedule_id=test_rehearsal_schedule.id,
        date=datetime.now(UTC) + timedelta(days=1),
        duration_minutes=120,
        location="稽古場A",
        notes="第1幕の稽古",
    )
    db.add(rehearsal)
    await db.commit()
    await db.refresh(rehearsal)
    return rehearsal


@pytest.mark.asyncio
async def test_list_rehearsals(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """稽古一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/rehearsals",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "rehearsals" in data


@pytest.mark.asyncio
async def test_create_rehearsal(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_rehearsal_schedule: RehearsalSchedule,
    test_user_token: str,
) -> None:
    """稽古作成のテスト."""
    # Arrange
    rehearsal_data = {
        "date": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        "duration_minutes": 90,
        "location": "稽古場B",
        "notes": "通し稽古",
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
async def test_update_rehearsal(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """稽古更新のテスト."""
    # Arrange
    update_data = {
        "location": "稽古場C",
        "notes": "更新された稽古内容",
        "duration_minutes": 150,
    }
    
    # Act
    response = await client.put(
        f"/api/rehearsals/{test_rehearsal.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_rehearsal(
    client: AsyncClient,
    test_user: User,
    test_rehearsal: Rehearsal,
    test_user_token: str,
) -> None:
    """稽古削除のテスト."""
    # Act
    response = await client.delete(
        f"/api/rehearsals/{test_rehearsal.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
