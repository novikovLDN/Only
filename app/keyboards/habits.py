"""Habits keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def back_only(lang: str, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=callback_data)]
        ]
    )


def habits_list(habits: list[tuple[int, str]], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"habit_{hid}")]
        for hid, title in habits
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
