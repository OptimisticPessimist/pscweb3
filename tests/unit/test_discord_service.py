"""DiscordServiceのユニットテスト."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import Response

from src.services.discord import DiscordService


@pytest.fixture
def discord_service() -> DiscordService:
    """DiscordServiceフィクスチャ."""
    return DiscordService()


@pytest.mark.asyncio
async def test_send_notification_success(discord_service: DiscordService):
    """通知送信が成功することを確認."""
    webhook_url = "https://discord.com/api/webhooks/test/test"
    content = "Test notification"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Response(204)
        
        await discord_service.send_notification(content, webhook_url=webhook_url)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == webhook_url
        assert kwargs["json"] == {"content": content}


@pytest.mark.asyncio
async def test_send_notification_no_url(discord_service: DiscordService):
    """URLがない場合は送信されないこと."""
    discord_service.default_webhook_url = None
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await discord_service.send_notification("Test")
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_invalid_url(discord_service: DiscordService):
    """不正なURLの場合は送信されないこと."""
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await discord_service.send_notification("Test", webhook_url="http://example.com/invalid")
        mock_post.assert_not_called()
