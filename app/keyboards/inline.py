"""Inline keyboards — ONLY InlineKeyboardMarkup in project."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_select(with_back: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
    ]
    if with_back:
        back_text = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
        rows.append([InlineKeyboardButton(text=back_text, callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu(lang: str, t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("add_habit"), callback_data="add_habit")],
        [InlineKeyboardButton(text=t("edit_habits"), callback_data="edit_habits")],
        [InlineKeyboardButton(text=t("loyalty_program"), callback_data="loyalty")],
        [InlineKeyboardButton(text=t("settings"), callback_data="settings")],
    ])


def back_inline(lang: str, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    text = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback_data)],
    ])


def settings_menu(lang: str, t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("profile"), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("choose_language"), callback_data="settings_lang")],
        [InlineKeyboardButton(text=t("back"), callback_data="back_main")],
    ])


def buy_subscription_inline(lang: str, t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("buy_subscription"), callback_data="to_subscription")],
        [InlineKeyboardButton(text=t("back"), callback_data="back_main")],
    ])
