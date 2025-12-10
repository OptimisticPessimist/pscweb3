"""Discord通知サービス."""

import httpx
from structlog import get_logger

from src.config import settings

logger = get_logger(__name__)


class DiscordService:
    """Discord通知を送信するサービス."""

    def __init__(self) -> None:
        """初期化."""
        self.default_webhook_url = settings.discord_webhook_url
        self.bot_token = settings.discord_bot_token
        self.api_base = "https://discord.com/api/v10"

    async def send_notification(
        self,
        content: str,
        webhook_url: str | None = None,
        embeds: list[dict] | None = None,
        file: dict | None = None,
    ) -> None:
        """Discordに通知を送信 (Webhook)."""
        target_url = webhook_url or self.default_webhook_url

        if not target_url or "discord.com/api/webhooks" not in target_url:
            logger.warning("Invalid or missing Discord Webhook URL", url=target_url)
            return

        try:
            async with httpx.AsyncClient() as client:
                if file:
                    import json
                    
                    payload_dict = {"content": content}
                    if embeds:
                        payload_dict["embeds"] = embeds
                    
                    data = {"payload_json": json.dumps(payload_dict)}
                    files = {"file": (file["filename"], file["content"])}
                    
                    response = await client.post(target_url, data=data, files=files)
                else:
                    payload = {"content": content}
                    if embeds:
                        payload["embeds"] = embeds
                    response = await client.post(target_url, json=payload)
                
                response.raise_for_status()
                logger.info("Discord notification sent", url=target_url)

        except httpx.HTTPError as e:
            logger.error("Failed to send Discord notification", error=str(e))
        except Exception as e:
            logger.error("Unexpected error sending Discord notification", error=str(e))

    async def send_channel_message(
        self,
        channel_id: str,
        content: str,
        embeds: list[dict] | None = None,
        components: list[dict] | None = None,
    ) -> dict | None:
        """チャンネルにメッセージを送信 (Bot)."""
        if not self.bot_token:
            logger.warning("Discord Bot Token not configured")
            return None

        url = f"{self.api_base}/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {self.bot_token}"}
        
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to send Discord channel message", error=str(e), channel_id=channel_id)
            return None

    async def get_reactions(self, channel_id: str, message_id: str, emoji: str) -> list[str]:
        """リアクションをしたユーザーのIDリストを取得."""
        if not self.bot_token:
            return []

        import urllib.parse
        encoded_emoji = urllib.parse.quote(emoji)
        
        url = f"{self.api_base}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}"
        headers = {"Authorization": f"Bot {self.bot_token}"}
        
        all_users = []
        after = None
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    params = {"limit": 100}
                    if after:
                        params["after"] = after
                        
                    response = await client.get(url, headers=headers, params=params)
                    if response.status_code == 404:
                        logger.warning("Message or emoji not found", message_id=message_id)
                        break
                    response.raise_for_status()
                    
                    users = response.json()
                    if not users:
                        break
                        
                    all_users.extend([u["id"] for u in users])
                    after = users[-1]["id"]
                    if len(users) < 100:
                        break
                        
            return all_users

        except Exception as e:
            logger.error("Failed to get reactions", error=str(e))
            return []


def get_discord_service() -> DiscordService:
    """Discordサービスの依存関係."""
    return DiscordService()
