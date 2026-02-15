"""Reply keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu(t: callable) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("add_habit"))],
            [KeyboardButton(text=t("edit_habits"))],
            [KeyboardButton(text=t("loyalty_program"))],
            [KeyboardButton(text=t("settings"))],
        ],
        resize_keyboard=True,
    )


def back(t: callable) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("back"))]],
        resize_keyboard=True,
    )
