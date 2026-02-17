"""Timezone to flag + label mapping for profile display."""

TZ_FLAGS = {
    "Europe/Moscow": ("🇷🇺", "Moscow"),
    "Europe/London": ("🇬🇧", "London"),
    "America/New_York": ("🇺🇸", "New York"),
    "Asia/Dubai": ("🇦🇪", "Dubai"),
}


def get_tz_display(tz: str) -> tuple[str, str]:
    """Return (flag, label) for timezone. Fallback: (🌍, raw tz)."""
    return TZ_FLAGS.get((tz or "").strip(), ("🌍", (tz or "UTC").replace("_", " ")))
