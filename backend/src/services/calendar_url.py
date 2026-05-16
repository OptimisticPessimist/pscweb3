"""Google Calendar URL builder."""

from datetime import datetime
from urllib.parse import quote


def build_google_calendar_url(
    title: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str = "",
    location: str = "",
) -> str:
    """Build a Google Calendar event creation URL.

    Args:
        title: Event title.
        start_dt: Event start datetime (UTC-aware).
        end_dt: Event end datetime (UTC-aware).
        description: Event description.
        location: Event location.

    Returns:
        Google Calendar URL string.
    """
    start_str = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end_str = end_dt.strftime("%Y%m%dT%H%M%SZ")

    params = (
        f"action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={start_str}/{end_str}"
    )
    if description:
        params += f"&details={quote(description)}"
    if location:
        params += f"&location={quote(location)}"

    return f"https://calendar.google.com/calendar/render?{params}"
