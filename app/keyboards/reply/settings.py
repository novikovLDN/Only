from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def settings_kb(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        buttons = [
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🌐 Язык")],
            [KeyboardButton(text="⬅️ Назад")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="👤 Profile")],
            [KeyboardButton(text="🌐 Language")],
            [KeyboardButton(text="⬅️ Back")],
        ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )
