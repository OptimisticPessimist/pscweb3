"""リクエストロギングミドルウェア.

リクエストごとに一意なIDを付与し、実行時間を計測してログ出力します。
"""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """リクエストロギングミドルウェア."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """リクエスト処理のラッパー.

        Args:
            request: FastAPIリクエスト
            call_next: 次の処理へ

        Returns:
            Response: レスポンス
        """
        request_id = str(uuid.uuid4())

        # structlogのコンテキストにリクエストIDを設定
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)


        start_time = time.time()

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            # レスポンスログ
            logger.info(
                "Request processed",
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )

            # レスポンスヘッダーにリクエストIDを含める（デバッグ用）
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            process_time = time.time() - start_time

            logger.error(
                "Request failed",
                error=str(e),
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True,
            )
            raise e
