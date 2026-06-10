"""Discord OAuth APIのテスト."""

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.api.auth import (
    _discord_auth_error_redirect,
    _discord_oauth_error_detail,
    _discord_retry_after_seconds,
    _fetch_discord_token_standard,
    callback,
)


def test_discord_oauth_error_detail_for_expired_code() -> None:
    assert (
        _discord_oauth_error_detail({"error": "invalid_grant"})
        == "Discord認証の有効期限が切れたか、認証コードが既に使用されています。ログインからやり直してください"
    )


def test_discord_oauth_error_detail_for_invalid_client() -> None:
    assert (
        _discord_oauth_error_detail({"error": "invalid_client"})
        == "Discord認証の設定に問題があります。管理者に連絡してください"
    )


def test_discord_oauth_error_detail_does_not_expose_unknown_response() -> None:
    assert (
        _discord_oauth_error_detail(
            {
                "error": "unexpected",
                "error_description": "sensitive provider response",
            }
        )
        == "Discord認証に失敗しました。ログインからやり直してください"
    )


def test_discord_oauth_error_detail_handles_missing_response() -> None:
    assert (
        _discord_oauth_error_detail(None)
        == "Discord認証に失敗しました。ログインからやり直してください"
    )


def test_discord_retry_after_prefers_header() -> None:
    assert (
        _discord_retry_after_seconds(
            {"Retry-After": "120"},
            {"retry_after": 30},
            fallback=2,
        )
        == 120
    )


def test_discord_retry_after_uses_response_body() -> None:
    assert _discord_retry_after_seconds({}, {"retry_after": 45.5}, fallback=2) == 45.5


def test_rate_limit_redirect_includes_wait_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.api.auth.settings.frontend_url", "https://example.com/")
    response = _discord_auth_error_redirect(
        HTTPException(status_code=429, detail="rate limited", headers={"Retry-After": "120"})
    )

    assert response.status_code == 307
    assert response.headers["location"] == (
        "https://example.com/login?auth_error=rate_limited&retry_after=120"
    )


@pytest.mark.asyncio
async def test_callback_redirects_missing_code_to_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.api.auth.settings.frontend_url", "https://example.com")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/auth/callback",
            "query_string": b"",
        }
    )

    response = await callback(request, db=None)

    assert response.headers["location"] == "https://example.com/login?auth_error=failed"


@pytest.mark.asyncio
async def test_callback_redirects_rate_limit_to_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def raise_rate_limit(code: str) -> dict:
        raise HTTPException(
            status_code=429,
            detail="rate limited",
            headers={"Retry-After": "600"},
        )

    monkeypatch.setattr("src.api.auth.settings.frontend_url", "https://example.com")
    monkeypatch.setattr("src.api.auth._fetch_discord_token_standard", raise_rate_limit)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/auth/callback",
            "query_string": b"code=test-code",
        }
    )

    response = await callback(request, db=None)

    assert response.headers["location"] == (
        "https://example.com/login?auth_error=rate_limited&retry_after=600"
    )


@pytest.mark.asyncio
async def test_long_discord_rate_limit_does_not_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def post(self, url, data):
            request = httpx.Request("POST", url)
            return httpx.Response(
                429,
                headers={"Retry-After": "600"},
                json={"message": "The resource is being rate limited.", "retry_after": 600},
                request=request,
            )

    async def fail_if_called(delay: float) -> None:
        pytest.fail(f"long rate limit must not sleep inside callback: {delay}")

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr("asyncio.sleep", fail_if_called)

    with pytest.raises(HTTPException) as exc_info:
        await _fetch_discord_token_standard("test-code")

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers == {"Retry-After": "600"}


@pytest.mark.asyncio
async def test_short_discord_rate_limit_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        post_count = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def post(self, url, data):
            self.post_count += 1
            request = httpx.Request("POST", url)
            if self.post_count == 1:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "1"},
                    json={"retry_after": 1},
                    request=request,
                )
            return httpx.Response(
                200,
                json={"access_token": "discord-token"},
                request=request,
            )

        async def get(self, url, headers):
            request = httpx.Request("GET", url)
            return httpx.Response(
                200,
                json={"id": "123", "username": "test-user"},
                request=request,
            )

    sleep_delays: list[float] = []

    async def record_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    fake_client = FakeClient()
    monkeypatch.setattr(httpx, "AsyncClient", lambda: fake_client)
    monkeypatch.setattr("asyncio.sleep", record_sleep)

    result = await _fetch_discord_token_standard("test-code")

    assert sleep_delays == [1]
    assert fake_client.post_count == 2
    assert result["token"]["access_token"] == "discord-token"
    assert result["user"]["id"] == "123"
