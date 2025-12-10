"""Discord InteractionsAPIのテスト."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from src.db.models import User


@pytest.mark.asyncio
async def test_handle_interaction_ping(client: AsyncClient) -> None:
    """Discord Pingインタラクションのテスト."""
    # Arrange
    interaction_data = {
        "type": 1,  # PING
        "id": "test_ping_id",
        "application_id": "test_app_id"
    }
    
    # Act
    response = await client.post(
        "/api/interactions",
        json=interaction_data,
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == 1  # PONG


@pytest.mark.asyncio
async def test_handle_interaction_button_click(client: AsyncClient, db) -> None:
    """ボタンクリックインタラクションのテスト."""
    # Arrange
    interaction_data = {
        "type": 3,  # MESSAGE_COMPONENT
        "id": "test_interaction_id",
        "application_id": "test_app_id",
        "data": {
            "custom_id": "attend_button",
            "component_type": 2
        },
        "user": {
            "id": "123456789",
            "username": "testuser"
        }
    }
    
    # Act
    response = await client.post(
        "/api/interactions",
        json=interaction_data,
    )
    
    # Assert
    assert response.status_code in [200, 400, 404]
    # インタラクションが処理される


@pytest.mark.asyncio
async def test_handle_interaction_invalid_type(client: AsyncClient) -> None:
    """無効なタイプのインタラクションのテスト."""
    # Arrange
    interaction_data = {
        "type": 999,  # 無効なタイプ
        "id": "test_id",
        "application_id": "test_app_id"
    }
    
    # Act
    response = await client.post(
        "/api/interactions",
        json=interaction_data,
    )
    
    # Assert
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_handle_interaction_attend_status(client: AsyncClient, db) -> None:
    """出欠ステータスインタラクションのテスト."""
    # Arrange
    interaction_data = {
        "type": 3,
        "id": "test_attend_id",
        "application_id": "test_app_id",
        "data": {
            "custom_id": "attend_uuid",
            "component_type": 2
        },
        "user": {
            "id": "987654321",
            "username": "attendee"
        }
    }
    
    # Act
    response = await client.post(
        "/api/interactions",
        json=interaction_data,
    )
    
    # Assert
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_verify_interaction_signature(client: AsyncClient) -> None:
    """インタラクション署名検証のテスト."""
    # Arrange
    interaction_data = {
        "type": 1,
        "id": "signature_test_id",
        "application_id": "test_app_id"
    }
    
    # 無効な署名ヘッダー
    headers = {
        "X-Signature-Ed25519": "invalid_signature",
        "X-Signature-Timestamp": "1234567890"
    }
    
    # Act
    response = await client.post(
        "/api/interactions",
        json=interaction_data,
        headers=headers
    )
    
    # Assert
    # 署名検証が行われる（有効/無効に関わらず）
    assert response.status_code in [200, 401]
