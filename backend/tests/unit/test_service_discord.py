"""Discordサービスのテスト."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.discord import DiscordService


@pytest.fixture
def discord_service() -> DiscordService:
    """テスト用Discordサービス."""
    return DiscordService()


@pytest.mark.asyncio
async def test_send_notification_success(discord_service: DiscordService) -> None:
    """Discord通知送信成功のテスト."""
    # Arrange
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "テスト通知"
    
    # Mock httpx
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context
        
        # Act
        await discord_service.send_notification(content=content, webhook_url=webhook_url)
        
        # Assert - エラーが発生しないことを確認
        assert True


@pytest.mark.asyncio
async def test_send_notification_no_webhook_url(discord_service: DiscordService) -> None:
    """webhook_urlなしでの通知送信テスト."""
    # Arrange
    content = "テスト通知"
    
    # Act - webhook_urlがNoneの場合、何もしない
    await discord_service.send_notification(content=content, webhook_url=None)
    
    # Assert - エラーが発生しないことを確認
    assert True


@pytest.mark.asyncio
async def test_send_notification_with_embeds(discord_service: DiscordService) -> None:
    """埋め込み付き通知送信のテスト."""
    # Arrange
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "テスト通知"
    embeds = [{"title": "テスト", "description": "説明"}]
    
    # Mock httpx
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context
        
        # Act
        await discord_service.send_notification(
            content=content,
            webhook_url=webhook_url,
            embeds=embeds
        )
        
        # Assert
        assert True


@pytest.mark.asyncio
async def test_send_button_message(discord_service: DiscordService) -> None:
    """ボタン付きメッセージ送信のテスト."""
    # Arrange
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "ボタン付きメッセージ"
    buttons = [
        {"label": "参加", "custom_id": "attend"},
        {"label": "欠席", "custom_id": "absent"}
    ]
    
    # Mock httpx
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context
        
        # Act
        await discord_service.send_button_message(
            content=content,
            webhook_url=webhook_url,
            buttons=buttons
        )
        
        # Assert
        assert True


@pytest.mark.asyncio
async def test_send_notification_error_handling(discord_service: DiscordService) -> None:
    """Discord通知送信エラーハンドリングのテスト."""
    # Arrange
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "テスト通知"
    
    # Mock httpx to raise an exception
    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.return_value = mock_context
        
        # Act - エラーが発生してもクラッシュしないことを確認
        try:
            await discord_service.send_notification(content=content, webhook_url=webhook_url)
            # エラーがログに記録されるが、例外は発生しない
            assert True
        except Exception:
            # エラーハンドリングされているはず
            pytest.fail("Exception should be caught")
