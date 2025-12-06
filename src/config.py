"""アプリケーション設定モジュール."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定.
    
    環境変数から設定を読み込む。
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # データベース
    database_url: str

    # Discord OAuth
    discord_client_id: str
    discord_client_secret: str
    discord_redirect_uri: str
    discord_bot_token: str | None = None
    discord_webhook_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7日間

    # Azure Blob Storage
    azure_storage_connection_string: str
    azure_storage_container_name: str = "scripts"

    # 環境
    environment: str = "development"


settings = Settings()
