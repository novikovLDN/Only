"""Settings, language, timezone keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def lang_select(next_step: str = "tz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data=f"lang_ru_{next_step}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data=f"lang_en_{next_step}",
                )
            ],
        ]
    )


def tz_select(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "tz_utc"), callback_data="tz_UTC")],
            [InlineKeyboardButton(text=t(lang, "tz_moscow"), callback_data="tz_Europe/Moscow")],
            [InlineKeyboardButton(text=t(lang, "tz_london"), callback_data="tz_Europe/London")],
            [InlineKeyboardButton(text=t(lang, "tz_dubai"), callback_data="tz_Asia/Dubai")],
            [InlineKeyboardButton(text=t(lang, "tz_almaty"), callback_data="tz_Asia/Almaty")],
            [InlineKeyboardButton(text=t(lang, "tz_ny"), callback_data="tz_America/New_York")],
            [InlineKeyboardButton(text=t(lang, "tz_other"), callback_data="tz_other")],
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
