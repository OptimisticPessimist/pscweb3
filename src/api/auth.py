"""認証APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.auth.discord import get_discord_user_info, get_or_create_user_from_discord, oauth
from src.auth.jwt import create_access_token
from src.config import settings
from src.db import get_db
from src.schemas.auth import TokenResponse, UserResponse

router = APIRouter()


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Discord OAuth ログイン開始.

    Args:
        request: FastAPI リクエスト

    Returns:
        RedirectResponse: Discord 認証ページへのリダイレクト
    """
    redirect_uri = settings.discord_redirect_uri
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@router.get("/callback", response_model=TokenResponse)
async def callback(request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Discord OAuth コールバック.

    Discord認証後のコールバックを処理し、JWT トークンを発行。

    Args:
        request: FastAPI リクエスト
        db: データベースセッション

    Returns:
        TokenResponse: JWT トークン

    Raises:
        HTTPException: 認証エラー
    """
    try:
        token = await oauth.discord.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Discord 認証エラー: {e}")

    # Discord ユーザー情報を取得
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="アクセストークンが取得できませんでした")

    discord_user_data = await get_discord_user_info(access_token)

    # ユーザーを取得または作成
    user = await get_or_create_user_from_discord(discord_user_data, db)

    # JWT トークンを生成
    jwt_token = create_access_token({"sub": user.id})

    return TokenResponse(access_token=jwt_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token: str, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """現在のユーザー情報を取得.

    Args:
        token: JWT トークン（クエリパラメータ）
        db: データベースセッション

    Returns:
        UserResponse: ユーザー情報

    Raises:
        HTTPException: 認証エラー
    """
    from src.auth.jwt import get_current_user

    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="無効なトークンです")

    return UserResponse.model_validate(user)
