"""データベース接続モジュール."""

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings


def _prepare_asyncpg_url(url: str) -> tuple[str, dict]:
    """asyncpgはsslmodeクエリパラメータを受け付けないため、connect_argsに変換する.

    sslmode=require は「暗号化必須・証明書検証なし」を意味するため、
    ssl=True（検証あり）ではなく SSLContext で verify_mode=CERT_NONE を設定する。
    """
    import ssl as _ssl

    connect_args: dict = {"statement_cache_size": 0}
    if "sslmode" not in url:
        return url, connect_args
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = params.pop("sslmode", [""])[0]
    if sslmode == "require":
        ssl_ctx = _ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = _ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query)), connect_args


_db_url, _connect_args = _prepare_asyncpg_url(settings.database_url)

# 非同期エンジンの作成
engine = create_async_engine(
    _db_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    # Supabase Transaction Pooler (PgBouncer) does not support prepared statements
    connect_args=_connect_args,
)

# 非同期セッションファクトリ
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """データベースセッションの依存性注入.

    Yields:
        AsyncSession: データベースセッション
    """
    async with async_session_maker() as session:
        yield session
