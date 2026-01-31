"""Habit-related keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.habit import Habit


def habits_list_keyboard(habits: list[Habit]) -> InlineKeyboardMarkup:
    """List of habits as inline buttons."""
    buttons = []
    for h in habits:
        emoji = h.emoji or "📌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {h.name}",
                callback_data=f"habit_select:{h.id}",
            ),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Новая привычка", callback_data="habit_new")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def habit_detail_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Single habit — log / edit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выполнено", callback_data=f"habit_done:{habit_id}"),
                InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"habit_skip:{habit_id}"),
            ],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"habit_edit:{habit_id}")],
        ]
    )
