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

    async def send_notification(
        self,
        content: str,
        webhook_url: str | None = None,
        embeds: list[dict] | None = None,
        file: dict | None = None,
    ) -> None:
        """Discordに通知を送信.

        Args:
            content: メッセージ本文
            webhook_url: 送信先Webhook URL (指定がなければデフォルト)
            embeds: 埋め込みメッセージ (オプション)
            file: 添付ファイル {"filename": str, "content": bytes} (オプション)
        """
        target_url = webhook_url or self.default_webhook_url

        if not target_url or "discord.com/api/webhooks" not in target_url:
            logger.warning("Invalid or missing Discord Webhook URL", url=target_url)
            return

        # multipart/form-data requests require specific handling
        if file:
            files = {
                "file": (file["filename"], file["content"])
            }
            # When sending files, payload_json field can be used for JSON data
            # OR we can just send data fields. 
            # httpx handles multipart if 'files' is provided.
            # We should pass 'content' and 'embeds' as data/json.
            
            # Simple approach: content is form field
            data = {"content": content}
            # embedded json is tricky in multipart in some libs, but Discord accepts 'payload_json'
            # Let's try simple fields first.
            
            # Note: with files, we use 'data' for non-file fields? 
            # Discord API says: parameters can be passed as form data.
            pass
        else:
            payload = {"content": content}
            if embeds:
                payload["embeds"] = embeds

        try:
            async with httpx.AsyncClient() as client:
                if file:
                    # Construct multipart request
                    import json
                    
                    payload_dict = {"content": content}
                    if embeds:
                        payload_dict["embeds"] = embeds
                    
                    # 'payload_json' is the key for the JSON part of the multipart body
                    data = {"payload_json": json.dumps(payload_dict)}
                    files = {"file": (file["filename"], file["content"])}
                    
                    response = await client.post(target_url, data=data, files=files)
                else:
                    response = await client.post(target_url, json=payload)
                
                response.raise_for_status()
                logger.info("Discord notification sent", url=target_url)


        except httpx.HTTPError as e:
            logger.error("Failed to send Discord notification", error=str(e))
        except Exception as e:
            logger.error("Unexpected error sending Discord notification", error=str(e))


def get_discord_service() -> DiscordService:
    """Discordサービスの依存関係."""
    return DiscordService()
