"""
Timezone-aware helpers for notifications.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Current UTC time."""
    return datetime.now(ZoneInfo("UTC"))


def to_user_tz(dt: datetime, tz_name: str) -> datetime:
    """Convert datetime to user's timezone."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(tz)


def parse_reminder_time(time_str: str, tz_name: str, base_date: datetime | None = None) -> datetime | None:
    """
    Parse HH:MM in user timezone to next occurrence as UTC datetime.
    base_date: reference date (default: now in user tz).
    """
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return None
    parts = time_str.split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
    except ValueError:
        return None
    base = base_date or datetime.now(tz)
    target = base.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= base:
        from datetime import timedelta
        target += timedelta(days=1)
    return target.astimezone(ZoneInfo("UTC"))
