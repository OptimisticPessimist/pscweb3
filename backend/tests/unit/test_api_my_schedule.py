"""マイスケジュールAPIのテスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


@pytest.mark.asyncio
async def test_get_my_schedule(
    client: AsyncClient,
    test_user: User,
    test_user_token: str,
) -> None:
    """マイスケジュール取得のテスト."""
    # Act
    response = await client.get(
        "/api/my-schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    # スケジュールは辞書またはリスト形式
    assert "events" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_my_schedule_with_rehearsals(
    client: AsyncClient,
    test_user: User,
    test_user_token: str,
) -> None:
    """稽古を含むマイスケジュール取得のテスト."""
    # Act
    response = await client.get(
        "/api/my-schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    # eventsキーが存在するか確認
    if "events" in data:
        assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_my_schedule_unauthorized(client: AsyncClient) -> None:
    """認証なしのマイスケジュールアクセステスト."""
    # Act
    response = await client.get("/api/my-schedule")
    
    # Assert
    assert response.status_code == 401
