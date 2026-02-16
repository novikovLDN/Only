"""Premium / subscription keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def premium_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "premium_1m"), callback_data="pay_1")],
            [InlineKeyboardButton(text=t(lang, "premium_3m"), callback_data="pay_3")],
            [InlineKeyboardButton(text=t(lang, "premium_6m"), callback_data="pay_6")],
            [InlineKeyboardButton(text=t(lang, "premium_12m"), callback_data="pay_12")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
