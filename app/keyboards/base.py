"""Universal Reply keyboard builder."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def build_menu(
    buttons: list[list[str]],
    resize_keyboard: bool = True,
    one_time_keyboard: bool = False,
    placeholder: str | None = "Select option...",
) -> ReplyKeyboardMarkup:
    """Build ReplyKeyboardMarkup from 2D list of button labels."""
    keyboard = [[KeyboardButton(text=btn) for btn in row] for row in buttons]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard,
        one_time_keyboard=one_time_keyboard,
        input_field_placeholder=placeholder,
    )
