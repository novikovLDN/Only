"""
Timezone-aware helpers for notifications.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Регионы для выбора timezone
TIMEZONE_REGIONS = {
    "europe": "🌍 Европа",
    "asia": "🌍 Азия",
    "america": "🌍 Америка",
    "africa": "🌍 Африка",
    "australia": "🌍 Австралия",
}

# Популярные IANA timezones по регионам
TIMEZONE_BY_REGION: dict[str, list[str]] = {
    "europe": [
        "Europe/Moscow", "Europe/Kyiv", "Europe/Minsk", "Europe/Berlin",
        "Europe/London", "Europe/Paris", "Europe/Istanbul", "Europe/Warsaw",
        "Europe/Rome", "Europe/Madrid", "Europe/Amsterdam", "Europe/Athens",
        "Europe/Prague", "Europe/Budapest", "Europe/Bucharest", "Europe/Helsinki",
    ],
    "asia": [
        "Asia/Almaty", "Asia/Tashkent", "Asia/Yekaterinburg", "Asia/Novosibirsk",
        "Asia/Tbilisi", "Asia/Baku", "Asia/Yerevan", "Asia/Tbilisi",
        "Asia/Dubai", "Asia/Tehran", "Asia/Kolkata", "Asia/Bangkok",
        "Asia/Singapore", "Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul",
    ],
    "america": [
        "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
        "America/Toronto", "America/Mexico_City", "America/Sao_Paulo", "America/Buenos_Aires",
    ],
    "africa": [
        "Africa/Cairo", "Africa/Johannesburg", "Africa/Lagos", "Africa/Nairobi",
        "Africa/Casablanca", "Africa/Algiers",
    ],
    "australia": [
        "Australia/Sydney", "Australia/Melbourne", "Australia/Perth", "Australia/Brisbane",
        "Pacific/Auckland",
    ],
}


def format_timezone_display(tz_name: str) -> str:
    """Format timezone for display: 'UTC+3 (Europe/Moscow)'."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return tz_name
    now = datetime.now(tz)
    offset = now.utcoffset()
    if offset is None:
        return tz_name
    total_sec = int(offset.total_seconds())
    if total_sec == 0:
        offset_str = "UTC"
    else:
        hours = abs(total_sec) // 3600
        sign = "+" if total_sec > 0 else "-"
        offset_str = f"UTC{sign}{hours}"
    if tz_name in ("UTC", "GMT"):
        return offset_str
    return f"{offset_str} ({tz_name})"


def validate_timezone(value: str) -> str | None:
    """Validate IANA timezone (Europe/Moscow, UTC, etc). Returns tz name or None."""
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    # UTC special case
    if s.upper() in ("UTC", "GMT"):
        return "UTC"
    try:
        ZoneInfo(s)
        return s
    except Exception:
        return None


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
