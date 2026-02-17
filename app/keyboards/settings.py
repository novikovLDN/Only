"""Settings, language, timezone keyboards — 4 TZ only."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t

# 4 timezones only
TIMEZONES = {
    "Europe/Moscow": "🇷🇺 Moscow",
    "Europe/London": "🇬🇧 London",
    "America/New_York": "🇺🇸 New York",
    "Asia/Dubai": "🇦🇪 Dubai",
}


def timezone_keyboard(active_tz: str, lang: str = "ru", callback_prefix: str = "tz") -> InlineKeyboardMarkup:
    """4 TZ buttons + Back. active_tz gets 🟢. callback_prefix: 'tz' (settings) or 'tz_onboard' (onboarding)."""
    active_tz = (active_tz or "Europe/Moscow").strip()
    back_text = t(lang, "btn_back")
    back_cb = "settings" if callback_prefix == "tz" else "back_main"

    buttons = []
    for tz, label in TIMEZONES.items():
        text = f"🟢 {label}" if tz == active_tz else label
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"{callback_prefix}:{tz}"),
        ])
    buttons.append([
        InlineKeyboardButton(text=back_text, callback_data=back_cb),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lang_select(next_step: str = "tz", lang: str = "ru", back_callback: str | None = None) -> InlineKeyboardMarkup:
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


def tz_select(lang: str) -> InlineKeyboardMarkup:
    """Same 4 TZ for onboarding flow. Uses tz_onboard: callback."""
    return timezone_keyboard("Europe/Moscow", lang, callback_prefix="tz_onboard")


def settings_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_tz"), callback_data="settings_tz")],
            [InlineKeyboardButton(text=t(lang, "settings_lang"), callback_data="settings_lang")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
