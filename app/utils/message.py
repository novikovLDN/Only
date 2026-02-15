"""Message helpers — always attach inline keyboard."""

from aiogram.types import InlineKeyboardMarkup, Message


async def send_with_buttons(
    message: Message,
    text: str,
    keyboard: InlineKeyboardMarkup,
) -> None:
    """Send message with inline keyboard. Never send plain message."""
    await message.answer(text=text, reply_markup=keyboard)
