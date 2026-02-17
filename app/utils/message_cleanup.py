"""Auto-delete messages after delay."""

import asyncio

from aiogram.exceptions import TelegramBadRequest


async def delete_later(bot, chat_id: int, message_id: int, delay: int = 60) -> None:
    """Delete message after delay. Ignores if already deleted."""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass  # message already deleted or not found
