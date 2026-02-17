"""Main menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def main_menu(lang: str, is_premium: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_add_habit"), callback_data="add_habit")],
            [InlineKeyboardButton(text=t(lang, "btn_edit_habits"), callback_data="edit_habits")],
            [InlineKeyboardButton(text=t(lang, "btn_profile"), callback_data="profile")],
            [InlineKeyboardButton(text=t(lang, "btn_game"), callback_data="game")],
            [InlineKeyboardButton(text=t(lang, "btn_loyalty"), callback_data="loyalty")],
            [InlineKeyboardButton(text=t(lang, "btn_settings"), callback_data="settings")],
        ]
    )
