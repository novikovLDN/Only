"""Main menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import SUPPORT_URL, t


def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_add_habit"), callback_data="add_habit")],
            [InlineKeyboardButton(text=t(lang, "btn_my_habits"), callback_data="my_habits")],
            [InlineKeyboardButton(text=t(lang, "btn_profile"), callback_data="profile")],
            [InlineKeyboardButton(text=t(lang, "btn_settings"), callback_data="settings")],
            [InlineKeyboardButton(text=t(lang, "btn_subscription"), callback_data="subscription")],
            [InlineKeyboardButton(text=t(lang, "btn_support"), url=SUPPORT_URL)],
        ]
    )


def subscription_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "sub_buy_1"), callback_data="pay_1")],
            [InlineKeyboardButton(text=t(lang, "sub_buy_3"), callback_data="pay_3")],
            [InlineKeyboardButton(text=t(lang, "sub_buy_12"), callback_data="pay_12")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
        ]
    )
