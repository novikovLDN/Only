from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def buy_subscription_kb(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        btns = [
            [KeyboardButton(text="Купить подписку")],
            [KeyboardButton(text="⬅️ Назад")],
        ]
    else:
        btns = [
            [KeyboardButton(text="Buy subscription")],
            [KeyboardButton(text="⬅️ Back")],
        ]
    return ReplyKeyboardMarkup(
        keyboard=btns,
        resize_keyboard=True,
        is_persistent=True,
    )
