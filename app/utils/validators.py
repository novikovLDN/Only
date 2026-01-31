"""
Input validation — protection against injection and invalid data.
"""

import re
from typing import Any

# Max lengths for user input
MAX_HABIT_NAME = 100
MAX_HABIT_DESC = 500
MAX_DECLINE_NOTE = 300

# Pattern: only letters, digits, spaces, basic punctuation
SAFE_TEXT_PATTERN = re.compile(r"^[\w\s\-.,!?а-яА-ЯёЁa-zA-Z0-9]+$", re.UNICODE)

# Timezone: IANA format (e.g. Europe/Moscow)
TIMEZONE_PATTERN = re.compile(r"^[A-Za-z]+/[A-Za-z_]+$")

# Time HH:MM
TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def validate_habit_name(value: str) -> str | None:
    """Validate habit name. Returns cleaned string or None if invalid."""
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()[:MAX_HABIT_NAME]
    if not cleaned or not SAFE_TEXT_PATTERN.match(cleaned):
        return None
    return cleaned


def validate_habit_description(value: str | None) -> str | None:
    """Validate habit description."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()[:MAX_DECLINE_NOTE]
    if not cleaned:
        return None
    if not SAFE_TEXT_PATTERN.match(cleaned):
        return None
    return cleaned


def validate_timezone(value: str) -> str | None:
    """Validate IANA timezone."""
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not TIMEZONE_PATTERN.match(cleaned):
        return None
    try:
        import zoneinfo
        zoneinfo.ZoneInfo(cleaned)
        return cleaned
    except Exception:
        return None


def validate_time(value: str) -> str | None:
    """Validate HH:MM time format."""
    if not value or not isinstance(value, str):
        return None
    m = TIME_PATTERN.match(value.strip())
    return m.group(0) if m else None


def sanitize_for_db(value: Any) -> Any:
    """Escape/sanitize value for safe DB usage. SQLAlchemy parameterizes by default."""
    if value is None:
        return None
    if isinstance(value, str):
        return value[:1000]  # Limit length
    return value
