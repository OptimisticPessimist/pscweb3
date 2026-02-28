import json
import logging
import asyncio
from typing import Any
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient
from src.config import settings

logger = logging.getLogger(__name__)

class PremiumConfigService:
    """プレミアム機能設定を管理するサービス.
    
    Azure Blob Storageから設定を読み込み、メモリ上にキャッシュする。
    """
    
    _config: dict[str, Any] = {}
    _last_fetched: datetime | None = None
    _cache_duration = timedelta(minutes=5)
    _lock = asyncio.Lock()

    @classmethod
    async def get_config(cls) -> dict[str, Any]:
        """最新の設定を取得する."""
        async with cls._lock:
            now = datetime.now()
            if not cls._config or not cls._last_fetched or (now - cls._last_fetched) > cls._cache_duration:
                await cls.refresh_config()
        return cls._config

    @classmethod
    async def refresh_config(cls):
        """Blob Storageから設定を再読み込みする."""
        if not settings.azure_storage_connection_string:
            logger.warning("Azure Storage connection string not set. Using environment variable defaults.")
            cls._config = cls._get_default_config()
            cls._last_fetched = datetime.now()
            return

        try:
            blob_service_client = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
            container_client = blob_service_client.get_container_client(settings.premium_config_container)
            blob_client = container_client.get_blob_client(settings.premium_config_blob_name)

            if blob_client.exists():
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                cls._config = json.loads(content)
                logger.info("Premium settings loaded from Blob Storage.")
            else:
                logger.warning(f"Premium settings blob not found: {settings.premium_config_blob_name}. Using defaults.")
                cls._config = cls._get_default_config()
            
            cls._last_fetched = datetime.now()
        except Exception as e:
            logger.error(f"Failed to fetch premium settings from Blob: {e}")
            if not cls._config:
                cls._config = cls._get_default_config()
            cls._last_fetched = datetime.now()

    @classmethod
    def _get_default_config(cls) -> dict[str, Any]:
        """環境変数からデフォルト設定を生成する."""
        return {
            "tier1": {
                "password": settings.premium_password_tier1,
                "limit": settings.premium_project_limit_tier1
            },
            "tier2": {
                "password": settings.premium_password_tier2,
                "limit": settings.premium_project_limit_tier2
            },
            "test": {
                "password": settings.premium_password_test,
                "limit": settings.premium_project_limit_test
            },
            "default_limit": settings.default_project_limit
        }

    @classmethod
    async def get_limit_and_password(cls, tier: str) -> tuple[str | None, int]:
        """指定したティアのパスワードと上限を取得."""
        config = await cls.get_config()
        tier_data = config.get(tier, {})
        return tier_data.get("password"), tier_data.get("limit", 0)

    @classmethod
    async def get_default_limit(cls) -> int:
        """デフォルトの上限を取得."""
        config = await cls.get_config()
        return config.get("default_limit", settings.default_project_limit)
