"""ロガー機能の単体テスト."""

from src.core.logger import configure_logger, get_logger

# テスト実行前にロガーを構成
configure_logger()

def test_get_logger() -> None:
    """ロガー取得のテスト."""
    logger = get_logger("test_logger")
    assert logger is not None


def test_logger_output() -> None:
    """ログ出力のテスト (structlog.testing.capture_logsを使用)."""
    # structlogのテストヘルパーを使用してログをキャプチャ
    from structlog.testing import capture_logs

    with capture_logs() as cap_logs:
        logger = get_logger("test_output")
        logger.info("test message", key="value")

    assert len(cap_logs) >= 1
    assert cap_logs[0]["event"] == "test message"
    assert cap_logs[0]["key"] == "value"
    assert cap_logs[0]["log_level"] == "info"

