"""Discord OAuth APIのテスト."""

from src.api.auth import _discord_oauth_error_detail


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
