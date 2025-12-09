"""基本テスト - インポートチェック."""


def test_import_models() -> None:
    """モデルのインポートテスト."""
    from src.db.models import User, TheaterProject, Script
    
    assert User is not None
    assert TheaterProject is not None
    assert Script is not None


def test_basic_assertion() -> None:
    """基本的なアサーションテスト."""
    assert 1 + 1 == 2
    assert "test" == "test"
