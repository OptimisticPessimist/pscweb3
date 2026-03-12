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

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """指数バックオフ付きでリクエストを実行し、429エラー時はRetry-Afterに従って待機する."""
        max_retries = 3
        retry_count = 0

        # ファイルアップロードが含まれる場合があるため、タイムアウトを長めに設定（60秒）
        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                try:
                    response = await client.request(method, url, **kwargs)

                    if response.status_code == 429:
                        retry_count += 1
                        if retry_count > max_retries:
                            logger.error(
                                "Max retries exceeded for Discord API", url=url, status_code=429
                            )
                            return response

                        # レート制限の詳細をロギング
                        retry_after = response.headers.get("Retry-After")
                        logger.warning(
                            "Discord API Rate Limited (429)",
                            url=url,
                            retry_after=retry_after,
                            retry_count=retry_count,
                            response_body=response.text,
                            headers=dict(response.headers),
                        )

                        # 待機時間の決定
                        import asyncio

                        wait_seconds = float(retry_after) if retry_after else (2**retry_count)
                        logger.info(f"Waiting for {wait_seconds}s before retry...", url=url)
                        await asyncio.sleep(wait_seconds)
                        continue

                    return response

                except httpx.HTTPError as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        raise e
                    wait_seconds = 2**retry_count
                    logger.warning(
                        f"HTTP Error occurred, retrying in {wait_seconds}s...",
                        error=str(e),
                        url=url,
                    )
                    import asyncio

                    await asyncio.sleep(wait_seconds)

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
            if file:
                import json

                payload_dict = {"content": content}
                if embeds:
                    payload_dict["embeds"] = embeds
                data = {"payload_json": json.dumps(payload_dict)}
                files = {"file": (file["filename"], file["content"])}

                response = await self._request_with_retry(
                    "POST", target_url, data=data, files=files
                )
            else:
                payload = {"content": content}
                if embeds:
                    payload["embeds"] = embeds
                response = await self._request_with_retry("POST", target_url, json=payload)

            response.raise_for_status()
            logger.info("Discord notification sent", url=target_url)

        except httpx.HTTPStatusError as e:
            # HTTPエラーの場合はDiscordから返されるエラーボディ（JSON等）もログに出力する
            logger.error(
                "Failed to send Discord notification (HTTP Status Error)",
                status_code=e.response.status_code,
                error=str(e),
                response_body=e.response.text,
                url=target_url,
            )
        except Exception as e:
            logger.error("Failed to send Discord notification", error=str(e), url=target_url)

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
            response = await self._request_with_retry("POST", url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(
                "Failed to send Discord channel message", error=str(e), channel_id=channel_id
            )
            return None

    async def get_reactions(self, channel_id: str, message_id: str, emoji: str) -> list[str]:
        """リアクションをしたユーザーのIDリストを取得."""
        if not self.bot_token:
            return []

        import urllib.parse

        encoded_emoji = urllib.parse.quote(emoji)

        url = (
            f"{self.api_base}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}"
        )
        headers = {"Authorization": f"Bot {self.bot_token}"}

        all_users = []
        after = None

        try:
            while True:
                params = {"limit": 100}
                if after:
                    params["after"] = after

                response = await self._request_with_retry(
                    "GET", url, headers=headers, params=params
                )
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
