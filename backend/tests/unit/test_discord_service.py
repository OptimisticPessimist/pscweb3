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

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        import httpx
        mock_request.return_value = Response(204, request=httpx.Request("POST", webhook_url))
        
        await discord_service.send_notification(content, webhook_url=webhook_url)
        
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == webhook_url
        assert kwargs["json"] == {"content": content}


@pytest.mark.asyncio
async def test_send_notification_no_url(discord_service: DiscordService):
    """URLがない場合は送信されないこと."""
    discord_service.default_webhook_url = None
    
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        await discord_service.send_notification("Test")
        mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_invalid_url(discord_service: DiscordService):
    """不正なURLの場合は送信されないこと."""
    
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        await discord_service.send_notification("Test", webhook_url="http://example.com/invalid")
        mock_request.assert_not_called()
