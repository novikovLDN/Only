"""Safe edit: fallback to delete + send when edit_text fails (e.g. photo/emoji-only message)."""

import logging

logger = logging.getLogger(__name__)


async def safe_edit_or_send(cb, text: str, reply_markup=None) -> tuple[int, int] | None:
    """
    Safely edit message. If edit fails (no text, photo-only, deleted, etc.),
    delete the message and send a new one instead.
    Returns (chat_id, message_id) of the visible message, or None.
    """
    try:
        await cb.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
        return (cb.message.chat.id, cb.message.message_id)
    except Exception as e:
        logger.debug("edit_text failed, fallback to delete+send: %s", e)
        try:
            await cb.message.delete()
        except Exception:
            pass
        msg = await cb.message.answer(
            text=text,
            reply_markup=reply_markup,
        )
        return (msg.chat.id, msg.message_id) if msg else None
