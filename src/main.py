"""FastAPI メインアプリケーション."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.api import auth, castings, invitations, projects, rehearsals, scene_charts, scripts
from src.config import settings
from src.core.logger import configure_logger
from src.middleware.request_logging import RequestLoggingMiddleware

# ロガー初期化
configure_logger()


app = FastAPI(
    title="PSC Web 3 API",
    description="演劇制作管理システム - Fountain脚本管理、香盤表、稽古スケジュール",
    version="0.1.0",
)

# ミドルウェア登録 (実行順序: 下から上)
# 1. TrustedHostMiddlewareがあれば一番外側
# 2. ProxyHeadersMiddleware (Azure App Serviceなどのリバースプロキシ対応)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 3. RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)


# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router, prefix="/auth", tags=["認証"])
app.include_router(projects.router, prefix="/projects", tags=["プロジェクト"])
app.include_router(invitations.router, tags=["招待"])
app.include_router(scripts.router, prefix="/scripts", tags=["脚本"])
app.include_router(scene_charts.router, prefix="/scripts", tags=["香盤表"])
app.include_router(castings.router, prefix="/scripts", tags=["キャスティング"])
app.include_router(rehearsals.router, prefix="/rehearsals", tags=["稽古スケジュール"])


@app.get("/")
async def root() -> dict[str, str]:
    """ルートエンドポイント.

    Returns:
        dict[str, str]: ウェルカムメッセージ
    """
    return {"message": "PSC Web 3 API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """ヘルスチェックエンドポイント.

    Returns:
        dict[str, str]: ステータス
    """
    return {"status": "ok"}
