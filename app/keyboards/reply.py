"""Reply keyboards for habit confirm/decline flow."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def habit_confirm_decline(t) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn.confirm")),
                KeyboardButton(text=t("btn.decline")),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def decline_reasons(t) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("decline.reason_tired"))],
            [KeyboardButton(text=t("decline.reason_sick"))],
            [KeyboardButton(text=t("decline.reason_no_want"))],
            [KeyboardButton(text=t("decline.back"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
