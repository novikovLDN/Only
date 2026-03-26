"""Settings, language, timezone keyboards — expanded timezone support."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t

# Expanded timezone list grouped by region
TIMEZONES = {
    # Europe
    "Europe/Moscow": "🇷🇺 Moscow",
    "Europe/London": "🇬🇧 London",
    "Europe/Berlin": "🇩🇪 Berlin",
    "Europe/Paris": "🇫🇷 Paris",
    "Europe/Rome": "🇮🇹 Rome",
    "Europe/Madrid": "🇪🇸 Madrid",
    "Europe/Warsaw": "🇵🇱 Warsaw",
    "Europe/Istanbul": "🇹🇷 Istanbul",
    "Europe/Kiev": "🇺🇦 Kyiv",
    "Europe/Bucharest": "🇷🇴 Bucharest",
    "Europe/Athens": "🇬🇷 Athens",
    # Asia
    "Asia/Dubai": "🇦🇪 Dubai",
    "Asia/Almaty": "🇰🇿 Almaty",
    "Asia/Tashkent": "🇺🇿 Tashkent",
    "Asia/Tbilisi": "🇬🇪 Tbilisi",
    "Asia/Kolkata": "🇮🇳 Kolkata",
    "Asia/Bangkok": "🇹🇭 Bangkok",
    "Asia/Singapore": "🇸🇬 Singapore",
    "Asia/Shanghai": "🇨🇳 Shanghai",
    "Asia/Tokyo": "🇯🇵 Tokyo",
    "Asia/Seoul": "🇰🇷 Seoul",
    "Asia/Novosibirsk": "🇷🇺 Novosibirsk",
    "Asia/Vladivostok": "🇷🇺 Vladivostok",
    # Americas
    "America/New_York": "🇺🇸 New York",
    "America/Chicago": "🇺🇸 Chicago",
    "America/Denver": "🇺🇸 Denver",
    "America/Los_Angeles": "🇺🇸 Los Angeles",
    "America/Toronto": "🇨🇦 Toronto",
    "America/Sao_Paulo": "🇧🇷 São Paulo",
    # Oceania & Africa
    "Australia/Sydney": "🇦🇺 Sydney",
    "Pacific/Auckland": "🇳🇿 Auckland",
    "Africa/Cairo": "🇪🇬 Cairo",
    "UTC": "🌐 UTC",
}

# Popular timezones shown on the first page
POPULAR_TZ = [
    "Europe/Moscow", "Europe/London", "America/New_York", "Asia/Dubai",
    "Europe/Berlin", "Asia/Almaty", "Asia/Istanbul",
]

TZ_PER_PAGE = 8


def timezone_keyboard(
    active_tz: str,
    lang: str = "ru",
    callback_prefix: str = "tz",
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Paginated timezone keyboard with popular TZ on first page."""
    active_tz = (active_tz or "Europe/Moscow").strip()
    back_text = t(lang, "btn_back")
    back_cb = "settings" if callback_prefix == "tz" else "back_main"

    tz_list = list(TIMEZONES.items())
    total_pages = max(1, (len(tz_list) + TZ_PER_PAGE - 1) // TZ_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * TZ_PER_PAGE
    chunk = tz_list[start_idx : start_idx + TZ_PER_PAGE]

    buttons = []
    for tz, label in chunk:
        text_str = f"🟢 {label}" if tz == active_tz else label
        buttons.append([
            InlineKeyboardButton(text=text_str, callback_data=f"{callback_prefix}:{tz}"),
        ])

    # Pagination row
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(text="⬅️", callback_data=f"tz_page:{callback_prefix}:{page - 1}"))
        pagination.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(text="➡️", callback_data=f"tz_page:{callback_prefix}:{page + 1}"))
        buttons.append(pagination)

    buttons.append([
        InlineKeyboardButton(text=back_text, callback_data=back_cb),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lang_select(next_step: str = "tz", lang: str = "ru", back_callback: str | None = None) -> InlineKeyboardMarkup:
    lang = (lang or "ru")[:2].lower()
    if lang not in ("ru", "en", "ar"):
        lang = "ru"
    ru_label = "🟢 🇷🇺 Русский" if lang == "ru" else "🇷🇺 Русский"
    en_label = "🟢 🇬🇧 English" if lang == "en" else "🇬🇧 English"
    ar_label = "🟢 🇸🇦 العربية" if lang == "ar" else "🇸🇦 العربية"
    rows = [
        [InlineKeyboardButton(text=ru_label, callback_data=f"lang_ru_{next_step}")],
        [InlineKeyboardButton(text=en_label, callback_data=f"lang_en_{next_step}")],
        [InlineKeyboardButton(text=ar_label, callback_data=f"lang_ar_{next_step}")],
    ]
    if back_callback:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tz_select(lang: str) -> InlineKeyboardMarkup:
    """Timezone selection for onboarding flow."""
    return timezone_keyboard("Europe/Moscow", lang, callback_prefix="tz_onboard")


def settings_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_tz"), callback_data="settings_tz")],
            [InlineKeyboardButton(text=t(lang, "settings_lang"), callback_data="settings_lang")],
            [InlineKeyboardButton(text=t(lang, "btn_export"), callback_data="export_data")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
