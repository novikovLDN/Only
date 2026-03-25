"""Rate limiting middleware — per-user throttling."""

import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)

# Per-user: track (timestamp, count) in a sliding window
_user_hits: dict[int, list[float]] = defaultdict(list)

# Defaults: 10 requests per 5 seconds
RATE_LIMIT = 10
RATE_WINDOW = 5.0  # seconds


class RateLimitMiddleware(BaseMiddleware):
    """Simple in-memory rate limiter per Telegram user."""

    def __init__(self, limit: int = RATE_LIMIT, window: float = RATE_WINDOW):
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            from_user = getattr(event, "from_user", None)
            if from_user:
                user_id = from_user.id

        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        hits = _user_hits[user_id]

        # Clean old entries outside the window
        cutoff = now - self.window
        _user_hits[user_id] = [ts for ts in hits if ts > cutoff]
        hits = _user_hits[user_id]

        if len(hits) >= self.limit:
            logger.warning("Rate limit exceeded for user_id=%s (%d/%d in %.1fs)", user_id, len(hits), self.limit, self.window)
            if isinstance(event, CallbackQuery):
                await event.answer("Too many requests. Please wait.", show_alert=True)
            return None

        hits.append(now)
        return await handler(event, data)
