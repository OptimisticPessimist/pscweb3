"""Azure Functions のウォームアップ Timer のテスト."""

from types import SimpleNamespace

import pytest

import function_app


@pytest.mark.asyncio
async def test_keep_api_warm_runs_healthcheck() -> None:
    """ウォームアップ Timer が FastAPI のヘルスチェックを実行できる."""
    await function_app.keep_api_warm(SimpleNamespace(past_due=False))
