"""Reply keyboards for habit confirm/decline flow and main menu."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def main_menu_reply(t) -> ReplyKeyboardMarkup:
    """Main menu as reply keyboard for commands."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn.add_habit")),
                KeyboardButton(text=t("btn.edit_habits")),
            ],
            [
                KeyboardButton(text=t("btn.loyalty")),
                KeyboardButton(text=t("btn.subscribe")),
            ],
            [
                KeyboardButton(text=t("btn.settings")),
                KeyboardButton(text=t("btn.support")),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


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
