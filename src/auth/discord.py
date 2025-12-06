"""Discord OAuth 2.0 認証サービス."""

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import User

# OAuth クライアントの設定
oauth = OAuth()
oauth.register(
    name="discord",
    client_id=settings.discord_client_id,
    client_secret=settings.discord_client_secret,
    authorize_url="https://discord.com/api/oauth2/authorize",
    access_token_url="https://discord.com/api/oauth2/token",
    api_base_url="https://discord.com/api/",
    client_kwargs={"scope": "identify email"},
)


async def get_discord_user_info(access_token: str) -> dict[str, str]:
    """Discord APIからユーザー情報を取得.
    
    Args:
        access_token: Discord アクセストークン
        
    Returns:
        dict[str, str]: ユーザー情報
        
    Raises:
        httpx.HTTPError: API呼び出しエラー
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def get_or_create_user_from_discord(
    discord_user_data: dict[str, str], db: AsyncSession
) -> User:
    """Discord ユーザーデータからユーザーを取得または作成.
    
    Args:
        discord_user_data: Discord API から取得したユーザーデータ
        db: データベースセッション
        
    Returns:
        User: ユーザーオブジェクト
    """
    discord_id = discord_user_data["id"]

    # 既存ユーザーを検索
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()

    if user:
        # ユーザー情報を更新
        user.discord_username = discord_user_data.get("username", user.discord_username)
        user.email = discord_user_data.get("email", user.email)
    else:
        # 新規ユーザーを作成
        user = User(
            discord_id=discord_id,
            discord_username=discord_user_data.get("username", "Unknown"),
            email=discord_user_data.get("email"),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user
