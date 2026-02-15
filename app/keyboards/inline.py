"""Inline keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_select() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ])


def back_inline(callback_data: str = "back") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data=callback_data)],
    ])


def settings_menu(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("profile"), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("choose_language"), callback_data="settings_lang")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")],
    ])
