"""GoogleカレンダーURL生成のテスト."""

from datetime import UTC, datetime, timedelta

from src.services.calendar_url import build_google_calendar_url


def test_basic_url_generation() -> None:
    """基本的なURL生成."""
    start = datetime(2026, 3, 24, 10, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=2)

    url = build_google_calendar_url(
        title="稽古 - テスト公演",
        start_dt=start,
        end_dt=end,
        description="シーン: #1-1 オープニング\n場所: 稽古場A",
        location="稽古場A",
    )

    assert url.startswith("https://calendar.google.com/calendar/render?")
    assert "action=TEMPLATE" in url
    assert "dates=20260324T100000Z/20260324T120000Z" in url
    assert "text=" in url
    assert "details=" in url
    assert "location=" in url


def test_url_encoding_japanese() -> None:
    """日本語タイトルのURLエンコード."""
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)

    url = build_google_calendar_url(title="稽古", start_dt=start, end_dt=end)

    # URL-encoded Japanese text should be present
    assert "%E7%A8%BD%E5%8F%A4" in url


def test_optional_params_omitted() -> None:
    """descriptionとlocationが空の場合はパラメータを含めない."""
    start = datetime(2026, 6, 15, 14, 30, 0, tzinfo=UTC)
    end = start + timedelta(minutes=90)

    url = build_google_calendar_url(title="Test", start_dt=start, end_dt=end)

    assert "details=" not in url
    assert "location=" not in url


def test_optional_params_included() -> None:
    """descriptionとlocationが指定された場合はパラメータを含める."""
    start = datetime(2026, 6, 15, 14, 30, 0, tzinfo=UTC)
    end = start + timedelta(minutes=90)

    url = build_google_calendar_url(
        title="Test",
        start_dt=start,
        end_dt=end,
        description="Some details",
        location="Room A",
    )

    assert "details=" in url
    assert "location=" in url
