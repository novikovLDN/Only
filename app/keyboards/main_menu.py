"""
Main menu keyboards.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои привычки"), KeyboardButton(text="➕ Добавить привычку")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="💳 Баланс")],
            [KeyboardButton(text="👥 Рефералы")],
        ],
        resize_keyboard=True,
    )


def habit_reminder_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for habit reminder — done / decline."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сделал", callback_data=f"habit_done:{habit_id}"),
                InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"habit_skip:{habit_id}"),
            ],
        ]
    )
