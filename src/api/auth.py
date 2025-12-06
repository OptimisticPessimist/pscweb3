"""認証APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.auth.discord import get_discord_user_info, get_or_create_user_from_discord, oauth
from src.auth.jwt import create_access_token
from src.config import settings
from src.db import get_db
from src.schemas.auth import UserResponse

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


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    """Discord OAuth コールバック."""
    # OSに応じた方法でDiscordからトークンとユーザー情報を取得
    try:
        import sys
        code = request.query_params.get('code')
        if not code:
             raise HTTPException(status_code=400, detail="認証コードが見つかりません")

        if sys.platform == 'win32':
            auth_data = await _fetch_discord_token_windows(code)
        else:
            auth_data = await _fetch_discord_token_standard(code)

        token_data = auth_data.get("token")
        discord_user_data = auth_data.get("user")
        
        if not token_data or not discord_user_data:
             raise HTTPException(status_code=500, detail="認証データが不完全です")

    except HTTPException as he:
        raise he
    except Exception as e:
        from src.core.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Auth error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"認証処理中にエラーが発生しました: {e}")

    # ユーザーを取得または作成
    user = await get_or_create_user_from_discord(discord_user_data, db)
    
    # JWT トークンを生成
    jwt_token = create_access_token({"sub": str(user.id)})

    redirect_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=redirect_url)


async def _fetch_discord_token_windows(code: str) -> dict:
    """Windows環境用: 外部プロセスを使ってDiscord認証を行う."""
    import sys
    import os
    import uuid
    import time
    import subprocess
    import json
    import asyncio
    
    helper_script_path = os.path.join(os.path.dirname(__file__), "auth_helper.py")
    result_file = os.path.join(os.path.dirname(__file__), f"auth_result_{uuid.uuid4().hex}.json")
    
    # DETACHED_PROCESS flag
    DETACHED_PROCESS = 0x00000008
    
    cmd = [
        sys.executable, 
        helper_script_path,
        result_file,
        "https://discord.com/api/v10/oauth2/token",
        settings.discord_client_id,
        settings.discord_client_secret,
        settings.discord_redirect_uri,
        code
    ]
    
    subprocess.Popen(
        cmd,
        creationflags=DETACHED_PROCESS,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True
    )
    
    # ポーリング処理
    result = None
    start_time = time.time()
    timeout = 20.0
    
    while time.time() - start_time < timeout:
        if os.path.exists(result_file):
            await asyncio.sleep(0.5) 
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        result = json.loads(content)
                        break
            except Exception:
                pass
        await asyncio.sleep(0.5)
        
    if os.path.exists(result_file):
        try:
            os.remove(result_file)
        except:
            pass

    if not result:
            raise HTTPException(status_code=504, detail="認証ヘルパーが応答しませんでした")

    if 'error' in result:
        raise HTTPException(status_code=400, detail=f"認証エラー: {result['error']}")
        
    if result.get("status_code", 200) >= 400:
        raise HTTPException(status_code=400, detail=f"Discord API エラー: {result.get('body')}")
            
    return result


async def _fetch_discord_token_standard(code: str) -> dict:
    """標準環境用: httpxを使ってDiscord認証を行う."""
    import httpx
    
    token_endpoint = "https://discord.com/api/v10/oauth2/token"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.discord_redirect_uri,
        'client_id': settings.discord_client_id,
        'client_secret': settings.discord_client_secret
    }
    
    async with httpx.AsyncClient() as client:
        # 1. トークン交換
        resp = await client.post(token_endpoint, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("access_token")
        
        # 2. ユーザー情報取得
        user_resp = await client.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_resp.raise_for_status()
        discord_user_data = user_resp.json()

    return {
        "token": token_data,
        "user": discord_user_data
    }


