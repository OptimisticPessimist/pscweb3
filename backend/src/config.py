"""アプリケーション設定モジュール."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定.

    環境変数から設定を読み込む。テスト環境ではデフォルト値を使用。
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # データベース
    database_url: str = "sqlite+aiosqlite:///test.db"

    # Azure Storage
    azure_storage_connection_string: str | None = None
    premium_config_container: str = "config"
    premium_config_blob_name: str = "premium_settings.json"

    # Discord OAuth
    discord_client_id: str = "test_client_id"
    discord_client_secret: str = "test_client_secret"
    discord_redirect_uri: str = "http://localhost:8000/auth/callback"
    discord_bot_token: str | None = None
    discord_public_key: str | None = None # Interactions受信用
    discord_webhook_url: str = "https://discord.com/api/webhooks/test/test"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # JWT
    jwt_secret_key: str = "test-secret-key-for-testing"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7日間

    # 環境
    environment: str = "development"

    # プロジェクト作成制限
    default_project_limit: int = 1
    premium_project_limit_tier1: int = 3
    premium_project_limit_tier2: int = 5
    premium_project_limit_test: int = 99

    premium_password_tier1: str | None = None
    premium_password_tier2: str | None = None
    premium_password_test: str | None = "test-premium-pass-2026"


settings = Settings()
