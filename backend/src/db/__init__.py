"""データベース接続モジュール."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

# 非同期エンジンの作成
engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    # Supabase Transaction Pooler (PgBouncer) does not support prepared statements
    connect_args={"statement_cache_size": 0},
)

# 非同期セッションファクトリ
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションの依存性注入.

    Yields:
        AsyncSession: データベースセッション
    """
    async with async_session_maker() as session:
        yield session
