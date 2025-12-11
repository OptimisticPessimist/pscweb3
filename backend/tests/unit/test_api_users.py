"""ユーザーAPIのテスト."""

import pytest
from httpx import AsyncClient

from src.db.models import User


@pytest.mark.asyncio
async def test_get_current_user(
    client: AsyncClient, test_user: User, test_user_token: str
) -> None:
    """現在のユーザー情報取得のテスト."""
    # Act
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["discord_username"] == test_user.discord_username


@pytest.mark.asyncio
async def test_get_user_schedule(
    client: AsyncClient, test_user: User, test_user_token: str
) -> None:
    """ユーザーのスケジュール取得のテスト."""
    # Act
    response = await client.get(
        "/api/users/me/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data or "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_unauthorized_user_access(client: AsyncClient) -> None:
    """認証なしのユーザー情報アクセステスト."""
    # Act
    response = await client.get("/api/users/me")
    
    # Assert
    assert response.status_code in [401, 422]
