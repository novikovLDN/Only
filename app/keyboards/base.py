"""Unified inline keyboard factory — InlineKeyboardMarkup only."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def inline_kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """
    Build InlineKeyboardMarkup from rows.
    rows: [[(text, callback_data), ...], [(text, url), ...]]
    Use callback_data for buttons, or (text, "url:https://...") for URL buttons.
    """
    keyboard = []
    for row in rows:
        btns = []
        for item in row:
            text, data = item
            if isinstance(data, str) and data.startswith("url:"):
                btns.append(InlineKeyboardButton(text=text, url=data[4:]))
            else:
                btns.append(InlineKeyboardButton(text=text, callback_data=data))
        if btns:
            keyboard.append(btns)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
