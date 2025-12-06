"""ロギング用デコレータ."""

import functools
from typing import Any, Callable

from src.core.logger import get_logger

logger = get_logger(__name__)


def log_process(process_name: str) -> Callable:
    """処理の開始と終了をログ出力するデコレータ.

    Args:
        process_name: 処理名

    Returns:
        Callable: デコレータ
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Start {process_name}")
            try:
                result = await func(*args, **kwargs)
                logger.info(f"End {process_name}")
                return result
            except Exception as e:
                logger.error(f"Failed {process_name}", error=str(e))
                raise e
        return wrapper
    return decorator
