"""Parse admin duration strings: 30d, 2m, 10h, 15min."""

import re
from datetime import timedelta


def parse_admin_duration(text: str) -> timedelta | None:
    """Parse duration like 30d, 2m, 10h, 15min. Returns None if invalid."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().lower()
    m = re.match(r"^(\d+)\s*(d|day|days|m|month|months|h|hour|hours|min|minute|minutes)$", text)
    if not m:
        return None
    try:
        n = int(m.group(1))
    except ValueError:
        return None
    unit = m.group(2)
    if unit in ("d", "day", "days"):
        return timedelta(days=n)
    if unit in ("h", "hour", "hours"):
        return timedelta(hours=n)
    if unit in ("min", "minute", "minutes"):
        return timedelta(minutes=n)
    if unit in ("m", "month", "months"):
        return timedelta(days=n * 30)
    return None
