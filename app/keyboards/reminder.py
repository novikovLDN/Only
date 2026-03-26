"""Reminder keyboards — Done / Skip / Snooze."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def reminder_buttons(habit_id: int, lang: str = "en", show_snooze: bool = True) -> InlineKeyboardMarkup:
    rows = [
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
    if show_snooze:
        rows.append([
            InlineKeyboardButton(
                text=t(lang, "reminder_snooze_15"),
                callback_data=f"snooze:{habit_id}:15",
            ),
            InlineKeyboardButton(
                text=t(lang, "reminder_snooze_30"),
                callback_data=f"snooze:{habit_id}:30",
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def complete_all_button(habit_ids: list[int], lang: str = "en") -> InlineKeyboardMarkup:
    """Button to complete all pending habits at once."""
    ids_str = ",".join(str(h) for h in habit_ids)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(lang, "btn_complete_all"),
            callback_data=f"complete_all:{ids_str}",
        )],
    ])


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
