"""FastAPI メインアプリケーション."""

import sys
import asyncio

# サブプロセスを使用するため、Windowsのデフォルト（Proactor）を明示的に使用
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.api import auth, characters, invitations, projects, rehearsals, scene_charts, scripts, users
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

@app.on_event("startup")
async def startup_event():
    pass


# ミドルウェア登録 (実行順序: 下から上)
# 1. TrustedHostMiddlewareがあれば一番外側
# 2. ProxyHeadersMiddleware (Azure App Serviceなどのリバースプロキシ対応)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 2. SessionMiddleware (Authlibで必須)
# ローカル開発(http)でも動くように https_only=False, same_site="lax" を設定
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key, https_only=False, same_site="lax")

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
app.include_router(projects.router, prefix="/api/projects", tags=["プロジェクト"])
app.include_router(invitations.router, prefix="/api/invitations", tags=["招待"])
# 香盤表はscriptsの下 (scripts.routerより先に定義して、具体的なパスを優先させる)
app.include_router(scene_charts.router, prefix="/api/scripts", tags=["香盤表"]) 
app.include_router(scripts.router, prefix="/api/scripts", tags=["脚本"])
# キャスティングはprojectsの下
app.include_router(characters.router, prefix="/api/projects", tags=["キャスティング"])
app.include_router(rehearsals.project_router, prefix="/api/projects", tags=["稽古スケジュール"])
app.include_router(rehearsals.router, prefix="/api", tags=["稽古スケジュール"])
app.include_router(users.router, prefix="/api/users", tags=["ユーザー"])


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

# Force reload for DB schema update
