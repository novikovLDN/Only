"""Content filter middleware — sanitize + moderate all incoming text.

Runs BEFORE handler dispatch:
1. Input sanitization (Unicode, size, Zalgo, emoji bomb)
2. Content moderation (banned words/phrases)

If text is rejected, the middleware silently drops the update
(no response to the user — bot ignores prohibited messages).
"""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.utils.content_moderator import is_prohibited
from app.utils.input_sanitizer import sanitize_text, MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)


class ContentFilterMiddleware(BaseMiddleware):
    """Silently drop messages that fail sanitization or contain prohibited content."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        text = None

        if isinstance(event, Message):
            text = event.text or event.caption
        elif isinstance(event, CallbackQuery):
            # Callback data is controlled by the bot, no need to moderate
            return await handler(event, data)

        if text is None:
            # Non-text messages (photos, stickers, etc.) — pass through
            return await handler(event, data)

        # Layer 1: Size check — reject oversized payloads immediately
        if len(text) > MAX_MESSAGE_LENGTH:
            logger.warning(
                "Content filter: oversized message (%d chars) from user_id=%s — dropped",
                len(text),
                getattr(getattr(event, "from_user", None), "id", "?"),
            )
            return None

        # Layer 2: Unicode sanitization (NFC, invisible chars, Zalgo, emoji bomb)
        sanitized = sanitize_text(text)
        if sanitized is None:
            logger.warning(
                "Content filter: sanitization rejected text from user_id=%s — dropped",
                getattr(getattr(event, "from_user", None), "id", "?"),
            )
            return None

        # Layer 3: Banned content check
        if is_prohibited(sanitized):
            logger.warning(
                "Content filter: prohibited content from user_id=%s — dropped",
                getattr(getattr(event, "from_user", None), "id", "?"),
            )
            return None

        # Layer 4: Check display name for illegal content
        from_user = getattr(event, "from_user", None)
        if from_user:
            display_name = from_user.first_name or ""
            if from_user.last_name:
                display_name += " " + from_user.last_name
            if display_name and is_prohibited(display_name):
                logger.warning(
                    "Content filter: prohibited display name '%s' from user_id=%s — dropped",
                    display_name[:30], from_user.id,
                )
                return None

        return await handler(event, data)
