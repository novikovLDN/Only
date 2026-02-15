from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        buttons = [
            [KeyboardButton(text="➕ Добавить привычку")],
            [KeyboardButton(text="✏️ Редактировать привычки")],
            [KeyboardButton(text="🎁 Программа лояльности")],
            [KeyboardButton(text="⚙️ Настройки")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="➕ Add Habit")],
            [KeyboardButton(text="✏️ Edit Habits")],
            [KeyboardButton(text="🎁 Loyalty Program")],
            [KeyboardButton(text="⚙️ Settings")],
        ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )
