from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def back_kb(lang: str) -> ReplyKeyboardMarkup:
    text = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
        is_persistent=True,
    )
