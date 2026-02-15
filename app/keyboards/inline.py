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


def main_menu(lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить привычку", callback_data="add_habit")],
            [InlineKeyboardButton(text="✏️ Редактировать привычки", callback_data="edit_habits")],
            [InlineKeyboardButton(text="🎁 Программа лояльности", callback_data="loyalty")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="➕ Add Habit", callback_data="add_habit")],
            [InlineKeyboardButton(text="✏️ Edit Habits", callback_data="edit_habits")],
            [InlineKeyboardButton(text="🎁 Loyalty Program", callback_data="loyalty")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_inline(lang: str, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    text = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback_data)],
    ])


def settings_menu(lang: str, t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("profile"), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("choose_language"), callback_data="settings_lang")],
        [InlineKeyboardButton(
            text=("⬅️ Назад" if lang == "ru" else "⬅️ Back"),
            callback_data="back_main"
        )],
    ])


def buy_subscription_inline(lang: str, t) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("buy_subscription"), callback_data="to_subscription")],
        [InlineKeyboardButton(
            text=("⬅️ Назад" if lang == "ru" else "⬅️ Back"),
            callback_data="back_main"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
