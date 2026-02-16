"""Profile keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def profile_keyboard(lang: str, is_premium: bool = False) -> InlineKeyboardMarkup:
    premium_btn = t(lang, "btn_premium_extend") if is_premium else t(lang, "btn_premium")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_statistics"), callback_data="profile_statistics")],
            [InlineKeyboardButton(text=t(lang, "btn_achievements"), callback_data="profile_achievements")],
            [InlineKeyboardButton(text=premium_btn, callback_data="premium")],
            [InlineKeyboardButton(text=t(lang, "profile_missed"), callback_data="profile_missed")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
