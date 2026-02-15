from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def language_select_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
