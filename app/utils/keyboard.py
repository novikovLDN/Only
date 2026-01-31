"""
Utilities for InlineKeyboardMarkup comparison.

Избегает TelegramBadRequest "message is not modified"
путём вызова edit_reply_markup только при реальном изменении клавиатуры.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, Message


def _markup_to_dict(markup: "InlineKeyboardMarkup | None") -> dict | None:
    """Serialize markup to comparable dict. None → None."""
    if markup is None:
        return None
    return markup.model_dump(mode="json")


def keyboards_equal(
    current: "InlineKeyboardMarkup | None",
    new: "InlineKeyboardMarkup | None",
) -> bool:
    """
    Compare two reply_markup keyboards.
    Returns True if structurally identical (no edit needed).
    """
    c = _markup_to_dict(current)
    n = _markup_to_dict(new)
    if c is None and n is None:
        return True
    if c is None or n is None:
        return False
    return json.dumps(c, sort_keys=True) == json.dumps(n, sort_keys=True)


async def edit_reply_markup_if_changed(
    message: "Message",
    new_markup: "InlineKeyboardMarkup",
) -> bool:
    """
    Edit reply_markup only if it actually changed.
    Returns True if edited, False if skipped (no change).
    """
    current = message.reply_markup
    if keyboards_equal(current, new_markup):
        return False
    await message.edit_reply_markup(reply_markup=new_markup)
    return True
