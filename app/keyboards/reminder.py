"""Reminder keyboards — Done / Skip."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def reminder_buttons(habit_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "reminder_done"),
                    callback_data=f"habit_done:{habit_id}",
                ),
                InlineKeyboardButton(
                    text=t(lang, "reminder_skip"),
                    callback_data=f"habit_skip:{habit_id}",
                ),
            ]
        ]
    )


def skip_reasons(lang: str, habit_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "skip_tired"),
                    callback_data=f"skip_reason:{habit_id}:tired",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "skip_sick"),
                    callback_data=f"skip_reason:{habit_id}:sick",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "skip_no_want"),
                    callback_data=f"skip_reason:{habit_id}:no",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_back"),
                    callback_data=f"back_to_reminder:{habit_id}",
                )
            ],
        ]
    )
