"""Settings, language, timezone keyboards."""

from zoneinfo import available_timezones

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t

COMMON_TIMEZONES = [
    "UTC",
    "Europe/Moscow",
    "Europe/London",
    "Asia/Dubai",
    "Asia/Almaty",
    "Asia/Tashkent",
    "Asia/Bangkok",
    "America/New_York",
    "America/Los_Angeles",
]

_FULL_TZ_CACHE: list[str] | None = None


def _get_all_timezones() -> list[str]:
    global _FULL_TZ_CACHE
    if _FULL_TZ_CACHE is None:
        _FULL_TZ_CACHE = sorted(available_timezones())
    return _FULL_TZ_CACHE


def timezone_keyboard(current_tz: str, lang: str) -> InlineKeyboardMarkup:
    """Main timezone screen: common timezones + Other + Back."""
    current_tz = (current_tz or "UTC").strip()
    lang = "en" if (lang or "").lower() == "en" else "ru"
    back_text = t(lang, "btn_back")
    other_text = t(lang, "tz_other")

    buttons = []
    for tz in COMMON_TIMEZONES:
        tz_clean = tz.strip()
        label = f"🟢 {tz_clean}" if tz_clean == current_tz else tz_clean
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"tz_set:{tz_clean}"),
        ])

    buttons.append([
        InlineKeyboardButton(text=other_text, callback_data="tz_other"),
    ])
    buttons.append([
        InlineKeyboardButton(text=back_text, callback_data="settings"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timezone_full_keyboard(current_tz: str, page: int, lang: str) -> InlineKeyboardMarkup:
    """Full timezone list with pagination."""
    current_tz = (current_tz or "UTC").strip()
    all_tz = _get_all_timezones()
    page_size = 20
    start = page * page_size
    end = start + page_size
    chunk = all_tz[start:end]

    lang = "en" if (lang or "").lower() == "en" else "ru"
    back_text = t(lang, "btn_back")
    prev_text = "◀ Prev" if lang == "en" else "◀ Пред"
    next_text = "Next ▶" if lang == "en" else "След ▶"

    buttons = []
    for tz in chunk:
        tz_clean = tz.strip()
        label = f"🟢 {tz_clean}" if tz_clean == current_tz else tz_clean
        buttons.append([
            InlineKeyboardButton(text=label[:64], callback_data=f"tz_set:{tz_clean}"),
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text=prev_text, callback_data=f"tz_page:{page - 1}"))
    if end < len(all_tz):
        nav_row.append(InlineKeyboardButton(text=next_text, callback_data=f"tz_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text=back_text, callback_data="settings"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lang_select(next_step: str = "tz", lang: str = "ru", back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Language selection. If back_callback is set, add Back button (e.g. for settings)."""
    lang = "en" if (lang or "").lower() == "en" else "ru"
    ru_label = "🟢 🇷🇺 Русский" if lang == "ru" else "🇷🇺 Русский"
    en_label = "🟢 🇬🇧 English" if lang == "en" else "🇬🇧 English"
    rows = [
        [InlineKeyboardButton(text=ru_label, callback_data=f"lang_ru_{next_step}")],
        [InlineKeyboardButton(text=en_label, callback_data=f"lang_en_{next_step}")],
    ]
    if back_callback:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tz_select(lang: str, prefix: str = "tz_") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "tz_utc"), callback_data=f"{prefix}UTC")],
            [InlineKeyboardButton(text=t(lang, "tz_moscow"), callback_data=f"{prefix}Europe/Moscow")],
            [InlineKeyboardButton(text=t(lang, "tz_london"), callback_data=f"{prefix}Europe/London")],
            [InlineKeyboardButton(text=t(lang, "tz_dubai"), callback_data=f"{prefix}Asia/Dubai")],
            [InlineKeyboardButton(text=t(lang, "tz_almaty"), callback_data=f"{prefix}Asia/Almaty")],
            [InlineKeyboardButton(text=t(lang, "tz_ny"), callback_data=f"{prefix}America/New_York")],
            [InlineKeyboardButton(text=t(lang, "tz_other"), callback_data=f"{prefix}other")],
        ]
    )


def settings_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_tz"), callback_data="settings_tz")],
            [InlineKeyboardButton(text=t(lang, "settings_lang"), callback_data="settings_lang")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
