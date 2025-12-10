"""出欠確認APIのテスト."""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AttendanceEvent, ProjectMember, TheaterProject, User


@pytest.fixture
async def test_attendance_event(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> AttendanceEvent:
    """テスト用出欠確認イベント."""
    event = AttendanceEvent(
        project_id=test_project.id,
        title="テスト出欠確認",
        deadline=datetime.now(UTC) + timedelta(days=1),
        schedule_date=datetime.now(UTC) + timedelta(days=2),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@pytest.mark.asyncio
async def test_create_attendance_event(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """出欠確認イベント作成のテスト."""
    # Arrange
    event_data = {
        "title": "稽古出欠確認",
        "deadline": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "schedule_date": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        "location": "稽古場A",
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/attendance",
        json=event_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["title"] == event_data["title"]


@pytest.mark.asyncio
async def test_list_attendance_events(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_attendance_event: AttendanceEvent,
    test_user_token: str,
) -> None:
    """出欠確認イベント一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/attendance",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_attendance_event(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_attendance_event: AttendanceEvent,
    test_user_token: str,
) -> None:
    """出欠確認イベント詳細取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{test_attendance_event.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_attendance_event.id)


@pytest.mark.asyncio
async def test_update_attendance_status(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_attendance_event: AttendanceEvent,
    test_user_token: str,
) -> None:
    """出欠ステータス更新のテスト."""
    # Arrange
    status_data = {
        "status": "attend",
        "notes": "参加します",
    }
    
    # Act
    response = await client.patch(
        f"/api/projects/{test_project.id}/attendance/{test_attendance_event.id}/my-status",
        json=status_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
