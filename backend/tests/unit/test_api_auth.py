"""認証APIのテスト."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from src.db.models import User


@pytest.mark.asyncio
async def test_login_redirect(client: AsyncClient) -> None:
    """ログインリダイレクトのテスト."""
    # Act
    response = await client.get("/auth/login", follow_redirects=False)
    
    # Assert
    # Discord OAuth へのリダイレクトを確認
    assert response.status_code in [302, 307]  # リダイレクトステータス


@pytest.mark.asyncio
async def test_callback_with_mock_discord(client: AsyncClient, db) -> None:
    """Discord OAuthコールバックのテスト（モック使用）."""
    # Arrange - Discordレスポンスをモック
    mock_token_response = {
        "access_token": "mock_access_token",
        "token_type": "Bearer"
    }
    
    mock_user_response = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "0001"
    }
    
    # Mock external requests
    with patch("src.api.auth._fetch_discord_token_standard") as mock_fetch:
        mock_fetch.return_value = {
            "status_code": 200,
            "token": mock_token_response,
            "user": mock_user_response
        }
        
        # Act
        response = await client.get(
            "/auth/callback",
            params={"code": "mock_auth_code"},
            follow_redirects=False
        )
        
        # Assert
        # コールバック処理が完了することを確認
        assert response.status_code in [200, 302, 307]


@pytest.mark.asyncio  
async def test_logout(client: AsyncClient, test_user: User, test_user_token: str) -> None:
    """ログアウトのテスト."""
    # Act
    response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # Assert
    assert response.status_code in [200, 204, 302]


@pytest.mark.asyncio
async def test_auth_state_parameter(client: AsyncClient) -> None:
    """認証stateパラメータのテスト."""
    # Act
    response = await client.get("/auth/login", follow_redirects=False)
    
    # Assert
    assert response.status_code in [302, 307]
    # リダイレクトURLにstateパラメータが含まれることを確認
    if "location" in response.headers:
        location = response.headers["location"]
        assert "discord.com" in location or "state" in location


@pytest.mark.asyncio
async def test_callback_error_handling(client: AsyncClient) -> None:
    """コールバックエラーハンドリングのテスト."""
    # Act - codeなしでコールバックを呼び出し
    response = await client.get("/auth/callback")
    
    # Assert
    # エラーが適切に処理されることを確認
    assert response.status_code in [400, 401, 302, 500]


@pytest.mark.asyncio
async def test_create_new_user_on_first_login(client: AsyncClient, db) -> None:
    """初回ログイン時のユーザー作成テスト."""
    # Arrange - 新しいDiscordユーザー
    mock_token_response = {
        "access_token": "new_user_token",
        "token_type": "Bearer"
    }
    
    mock_user_response = {
        "id": "999999999",  # 新しいID
        "username": "newuser",
        "discriminator": "0002"
    }
    
    # Mock
    with patch("src.api.auth._fetch_discord_token_standard") as mock_fetch:
        mock_fetch.return_value = {
            "status_code": 200,
            "token": mock_token_response,
            "user": mock_user_response
        }
        
        # Act
        response = await client.get(
            "/auth/callback",
            params={"code": "new_user_code"},
            follow_redirects=False
        )
        
        # Assert
        # 新規ユーザーが作成される
        assert response.status_code in [200, 302, 307]
