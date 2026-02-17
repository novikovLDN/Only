"""Timezone validation and utilities."""

from zoneinfo import ZoneInfo


def validate_timezone(tz: str) -> bool:
    """Validate that timezone is a valid IANA name. Returns True if valid."""
    if not tz or not (tz := tz.strip()):
        return False
    try:
        ZoneInfo(tz)
        return True
    except Exception:
        return False
