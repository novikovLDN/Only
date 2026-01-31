"""
Message Lifecycle Manager — управление сообщениями в чате.

Правило: при нажатии на кнопку предыдущее сообщение удаляется (кроме sticky).
Исключения: profile, referral — не удалять.
"""

import logging
from typing import Any

from aiogram import Bot
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# user_id -> {message_id, chat_id, is_sticky}
_storage: dict[int, dict[str, Any]] = {}


def _get_key(user_id: int) -> dict | None:
    return _storage.get(user_id)


def _set_key(user_id: int, chat_id: int, message_id: int, is_sticky: bool) -> None:
    _storage[user_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "is_sticky": is_sticky,
    }


async def _try_delete(bot: Bot, chat_id: int, message_id: int) -> None:
    """Delete message, silently ignore errors."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.debug("Lifecycle delete skipped: %s", e)


async def send_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    sticky: bool = False,
) -> Message:
    """
    Send UI screen with lifecycle management.
    Deletes previous message unless it was sticky.
    """
    prev = _get_key(user_id)
    if prev and not prev.get("is_sticky"):
        await _try_delete(bot, prev["chat_id"], prev["message_id"])

    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )
    _set_key(user_id, chat_id, msg.message_id, sticky)
    return msg


def _extract_bot_chat_user(event: Message | CallbackQuery, user_id: int) -> tuple[Bot, int]:
    if isinstance(event, Message):
        return event.bot, event.chat.id
    return event.bot, event.message.chat.id


async def send_screen_from_event(
    event: Message | CallbackQuery,
    user_id: int,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    sticky: bool = False,
) -> Message:
    """Convenience: send screen from Message or CallbackQuery."""
    bot, chat_id = _extract_bot_chat_user(event, user_id)
    return await send_screen(bot, chat_id, user_id, text, reply_markup=reply_markup, sticky=sticky)
