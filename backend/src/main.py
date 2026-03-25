"""FastAPI メインアプリケーション."""

import asyncio
import os
import sys

# サブプロセスを使用するため、Windowsのデフォルト（Proactor）を明示的に使用
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.api import (
    attendance,
    auth,
    characters,
    dashboard,
    interactions,
    invitations,
    my_schedule,
    projects,
    public,
    rehearsals,
    reservations,
    scene_charts,
    schedule_polls,
    scripts,
    users,
)
from src.config import settings
from src.core.logger import configure_logger, get_logger
from src.middleware.request_logging import RequestLoggingMiddleware

# ロガー初期化
configure_logger()
logger = get_logger(__name__)

app = FastAPI(
    title="PSCWeb3 API",
    description="演劇制作管理システム - Fountain脚本管理、香盤表、稽古スケジュール",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    auto_migrate = settings.environment == "development" or os.getenv(
        "AUTO_MIGRATE_ON_STARTUP", "false"
    ).lower() in {"1", "true", "yes"}
    if not auto_migrate:
        return

    try:
        import subprocess
        from pathlib import Path

        backend_dir = Path(__file__).resolve().parents[1]
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(
                "Startup migration failed",
                returncode=process.returncode,
                stderr=stderr.decode(errors="ignore"),
            )
        else:
            logger.info("Startup migration completed", stdout=stdout.decode(errors="ignore"))
    except Exception as exc:
        logger.error("Startup migration crashed", error=str(exc), exc_info=True)


@app.get("/api/fix-system")
async def manual_fix_system():
    """システム修復用エンドポイント (Migration & Data Fix)."""
    log = []
    try:
        # 1. Run Migration
        import os
        import subprocess
        import sys

        # backend rootをパスに追加
        current_dir = os.path.dirname(os.path.abspath(__file__))  # src/
        backend_dir = os.path.dirname(current_dir)  # backend/
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)

        # 1-1. Alembic migration
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Alembic migration failed: {stderr.decode(errors='ignore')}")
        log.append("Alembic migration executed successfully.")

        # 1-2. Legacy SQL migration
        import apply_migration

        await apply_migration.apply_migration()
        log.append("Legacy SQL migration executed successfully.")

        # 2. Run Data Fix
        import fix_data_is_public

        report = await fix_data_is_public.fix_project_is_public()
        log.append("Data fix executed successfully.")

        return {"status": "success", "log": log, "report": report}
    except Exception as e:
        import traceback

        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


# ミドルウェア登録 (実行順序: 下から上)
# 1. TrustedHostMiddlewareがあれば一番外側
# 2. ProxyHeadersMiddleware (Azure App Serviceなどのリバースプロキシ対応)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 2. SessionMiddleware (Authlibで必須)
# ローカル開発(http)でも動くように https_only=False, same_site="lax" を設定
app.add_middleware(
    SessionMiddleware, secret_key=settings.jwt_secret_key, https_only=False, same_site="lax"
)

# 3. RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)


# CORS設定
# CORS設定
origins = []
if settings.environment == "development":
    origins.append("*")
if settings.frontend_url:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router, prefix="/api/auth", tags=["認証"])
app.include_router(projects.router, prefix="/api/projects", tags=["プロジェクト"])
app.include_router(invitations.router, prefix="/api", tags=["招待"])
app.include_router(attendance.router, prefix="/api/projects", tags=["出欠確認"])
app.include_router(public.router, prefix="/api/public", tags=["公開API"])
app.include_router(interactions.router, prefix="/api", tags=["Discord Interactions"])
# 香盤表はscriptsの下 (scripts.routerより先に定義して、具体的なパスを優先させる)
app.include_router(scene_charts.router, prefix="/api/scripts", tags=["香盤表"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["脚本"])
# キャスティングはprojectsの下
app.include_router(characters.router, prefix="/api/projects", tags=["キャスティング"])
app.include_router(rehearsals.project_router, prefix="/api/projects", tags=["稽古スケジュール"])
app.include_router(rehearsals.router, prefix="/api", tags=["稽古スケジュール"])
app.include_router(dashboard.router, prefix="/api/projects", tags=["ダッシュボード"])
app.include_router(my_schedule.router, prefix="/api", tags=["マイスケジュール"])
app.include_router(users.router, prefix="/api/users", tags=["ユーザー"])
app.include_router(reservations.router, prefix="/api", tags=["予約"])
app.include_router(schedule_polls.router, prefix="/api", tags=["日程調整"])


@app.get("/")
async def root() -> dict[str, str]:
    """ルートエンドポイント.

    Returns:
        dict[str, str]: ウェルカムメッセージ
    """
    return {"message": "PSC Web 3 API"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    """ヘルスチェックエンドポイント.

    Returns:
        dict[str, str]: ステータス
    """
    return {"status": "ok"}


# Force reload for DB schema update
