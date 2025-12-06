"""ロガー設定モジュール.

structlogを使用してJSON形式の構造化ログを出力します。
Azure Monitorなどのログ収集基盤での解析を容易にします。
"""

import logging
import os
import sys
from typing import Any

import structlog

# ログレベルの設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 標準ライブラリのlogging設定
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=LOG_LEVEL,
)


def configure_logger() -> None:
    """structlogの構成を行います."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    # 環境に応じたプロセッサの設定
    if os.getenv("APP_ENV") == "development":
        # 開発環境: コンソールで見やすい出力
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        # 本番環境: JSON出力 (Azure Logs等用)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """ロガーを取得します.

    Args:
        name: ロガー名

    Returns:
        Structured Logger
    """
    return structlog.get_logger(name)
