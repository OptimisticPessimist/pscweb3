"""認証APIエンドポイント."""

import math
from collections.abc import Mapping
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.auth.discord import get_or_create_user_from_discord, oauth
from src.auth.jwt import create_access_token
from src.config import settings
from src.db import get_db

router = APIRouter()
DISCORD_MAX_RETRIES = 3
DISCORD_MAX_INLINE_RETRY_AFTER_SECONDS = 5.0


def _discord_oauth_error_detail(response_body: Mapping[str, object] | None) -> str:
    """Discord OAuthエラーを利用者向けの安全なメッセージへ変換する."""
    error_code = response_body.get("error") if response_body else None
    if error_code == "invalid_grant":
        return "Discord認証の有効期限が切れたか、認証コードが既に使用されています。ログインからやり直してください"
    if error_code == "invalid_client":
        return "Discord認証の設定に問題があります。管理者に連絡してください"
    return "Discord認証に失敗しました。ログインからやり直してください"


def _discord_oauth_error_reason(response_body: Mapping[str, object] | None) -> str | None:
    """Discord OAuthエラーをフロントエンド向けの機械可読な理由コードへ変換する."""
    error_code = response_body.get("error") if response_body else None
    if error_code == "invalid_grant":
        return "expired"
    if error_code == "invalid_client":
        return "config"
    return None


def _discord_oauth_error_headers(response_body: Mapping[str, object] | None) -> dict[str, str] | None:
    """理由コードをHTTPExceptionヘッダーへ載せ、リダイレクト時に伝播できるようにする."""
    reason = _discord_oauth_error_reason(response_body)
    return {"X-Auth-Error-Reason": reason} if reason else None


def _discord_retry_after_seconds(
    headers: Mapping[str, str],
    response_body: Mapping[str, object] | None,
    fallback: float,
) -> float:
    """Discordの429レスポンスから再試行待機秒数を取得する."""
    raw_value: object | None = next(
        (value for key, value in headers.items() if key.casefold() == "retry-after"),
        None,
    )
    if raw_value is None and response_body:
        raw_value = response_body.get("retry_after")

    try:
        return max(0.0, float(raw_value)) if raw_value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def _discord_rate_limit_error(retry_after: float) -> HTTPException:
    """Discordのレート制限を再試行可能な認証エラーへ変換する."""
    retry_after_seconds = max(1, math.ceil(retry_after))
    return HTTPException(
        status_code=429,
        detail="Discord認証が混み合っています。しばらく待ってからログインし直してください",
        headers={"Retry-After": str(retry_after_seconds)},
    )


def _discord_auth_error_redirect(error: HTTPException) -> RedirectResponse:
    """認証失敗をフロントエンドのログイン画面へ安全に戻す."""
    params = {"auth_error": "rate_limited" if error.status_code == 429 else "failed"}
    error_headers = error.headers or {}
    retry_after = error_headers.get("Retry-After")
    if retry_after:
        params["retry_after"] = retry_after

    reason = error_headers.get("X-Auth-Error-Reason")
    if reason and error.status_code != 429:
        params["reason"] = reason

    login_url = f"{settings.frontend_url.rstrip('/')}/login?{urlencode(params)}"
    return RedirectResponse(url=login_url)


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Discord OAuth ログイン開始.

    Args:
        request: FastAPI リクエスト

    Returns:
        RedirectResponse: Discord 認証ページへのリダイレクト
    """
    redirect_uri = settings.discord_redirect_uri
    from src.core.logger import get_logger

    logger = get_logger(__name__)
    logger.info(f"Starting Discord login with redirect_uri: {redirect_uri}")
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    """Discord OAuth コールバック."""
    try:
        import sys

        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="認証コードが見つかりません")

        if sys.platform == "win32":
            auth_data = await _fetch_discord_token_windows(code)
        else:
            auth_data = await _fetch_discord_token_standard(code)

        token_data = auth_data.get("token")
        discord_user_data = auth_data.get("user")

        if not token_data or not discord_user_data:
            raise HTTPException(status_code=500, detail="認証データが不完全です")

        user = await get_or_create_user_from_discord(discord_user_data, db)
        jwt_token = create_access_token({"sub": str(user.id)})
        redirect_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
    except HTTPException as error:
        return _discord_auth_error_redirect(error)
    except Exception as e:
        from src.core.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Auth error: {str(e)}", exc_info=True)
        return _discord_auth_error_redirect(
            HTTPException(status_code=400, detail="Discord認証に失敗しました")
        )


async def _fetch_discord_token_windows(code: str) -> dict:
    """Windows環境用: 外部プロセスを使ってDiscord認証を行う."""
    import asyncio
    import json
    import os
    import subprocess
    import sys
    import time
    import uuid

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
        code,
    ]

    subprocess.Popen(
        cmd,
        creationflags=DETACHED_PROCESS,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )

    # ポーリング処理
    result = None
    start_time = time.time()
    timeout = 20.0

    while time.time() - start_time < timeout:
        if os.path.exists(result_file):
            await asyncio.sleep(0.5)
            try:
                with open(result_file, encoding="utf-8") as f:
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

    if "error" in result:
        raise HTTPException(status_code=400, detail=f"認証エラー: {result['error']}")

    status_code = int(result.get("status_code", 200))
    if status_code == 429:
        response_body = result.get("body")
        retry_after = _discord_retry_after_seconds(
            result.get("headers", {}),
            response_body if isinstance(response_body, dict) else None,
            fallback=5.0,
        )
        raise _discord_rate_limit_error(retry_after)

    if status_code >= 400:
        response_body = result.get("body")
        parsed_body = response_body if isinstance(response_body, dict) else None
        raise HTTPException(
            status_code=400,
            detail=_discord_oauth_error_detail(parsed_body),
            headers=_discord_oauth_error_headers(parsed_body),
        )

    return result


async def _fetch_discord_token_standard(code: str) -> dict:
    """標準環境用: httpxを使ってDiscord認証を行う."""
    import asyncio

    import httpx

    from src.core.logger import get_logger

    logger = get_logger(__name__)

    token_endpoint = "https://discord.com/api/v10/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
    }

    async with httpx.AsyncClient() as client:
        # 1. トークン交換 (リトライ付き)
        token_data = None
        for i in range(DISCORD_MAX_RETRIES + 1):
            resp = await client.post(token_endpoint, data=data)
            if resp.status_code == 429:
                try:
                    parsed_body = resp.json()
                except ValueError:
                    parsed_body = None
                response_body = parsed_body if isinstance(parsed_body, dict) else None
                retry_after = _discord_retry_after_seconds(
                    resp.headers,
                    response_body,
                    fallback=2 ** (i + 1),
                )
                can_retry_inline = (
                    i < DISCORD_MAX_RETRIES
                    and retry_after <= DISCORD_MAX_INLINE_RETRY_AFTER_SECONDS
                )
                logger.warning(
                    "Discord Token API Rate Limited (429)",
                    headers=dict(resp.headers),
                    body=resp.text,
                    retry_after=retry_after,
                    retrying=can_retry_inline,
                )
                if not can_retry_inline:
                    raise _discord_rate_limit_error(retry_after)
                await asyncio.sleep(retry_after)
                continue

            if resp.status_code >= 400:
                try:
                    parsed_body = resp.json()
                except ValueError:
                    parsed_body = None
                response_body = parsed_body if isinstance(parsed_body, dict) else None
                logger.error(
                    f"Discord Token API Error: {resp.status_code}",
                    body=resp.text,
                )
                raise HTTPException(
                    status_code=400,
                    detail=_discord_oauth_error_detail(response_body),
                    headers=_discord_oauth_error_headers(response_body),
                )

            token_data = resp.json()
            break

        if not token_data:
            raise HTTPException(status_code=502, detail="Discordトークンの取得に失敗しました")

        access_token = token_data.get("access_token")

        # 2. ユーザー情報取得 (リトライ付き)
        discord_user_data = None
        for i in range(DISCORD_MAX_RETRIES + 1):
            user_resp = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code == 429:
                try:
                    parsed_body = user_resp.json()
                except ValueError:
                    parsed_body = None
                response_body = parsed_body if isinstance(parsed_body, dict) else None
                retry_after = _discord_retry_after_seconds(
                    user_resp.headers,
                    response_body,
                    fallback=2 ** (i + 1),
                )
                can_retry_inline = (
                    i < DISCORD_MAX_RETRIES
                    and retry_after <= DISCORD_MAX_INLINE_RETRY_AFTER_SECONDS
                )
                logger.warning(
                    "Discord User Info API Rate Limited (429)",
                    headers=dict(user_resp.headers),
                    body=user_resp.text,
                    retry_after=retry_after,
                    retrying=can_retry_inline,
                )
                if not can_retry_inline:
                    raise _discord_rate_limit_error(retry_after)
                await asyncio.sleep(retry_after)
                continue

            if user_resp.status_code >= 400:
                logger.error(
                    f"Discord User Info API Error: {user_resp.status_code}", body=user_resp.text
                )

            user_resp.raise_for_status()
            discord_user_data = user_resp.json()
            break

    return {"token": token_data, "user": discord_user_data}
