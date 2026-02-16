"""Profile keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "profile_missed"), callback_data="profile_missed")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
