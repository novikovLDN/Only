"""Timezone validation — 4 zones only."""

from app.services.user_service import ALLOWED_TIMEZONES


def validate_timezone(tz: str) -> bool:
    """Returns True if tz is one of the 4 allowed."""
    return (tz or "").strip() in ALLOWED_TIMEZONES
