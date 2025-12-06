"""FastAPI メインアプリケーション."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, projects, scene_charts, scripts
from src.config import settings

app = FastAPI(
    title="PSC Web 3 API",
    description="演劇制作管理システム - Fountain脚本管理、香盤表、稽古スケジュール",
    version="0.1.0",
)

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
app.include_router(scripts.router, prefix="/scripts", tags=["脚本"])
app.include_router(scene_charts.router, prefix="/scripts", tags=["香盤表"])


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
