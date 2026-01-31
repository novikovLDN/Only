"""
Rate limiting middleware.
"""

from collections import defaultdict
from time import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, rate_limit: int | None = None) -> None:
        self.rate_limit = rate_limit or settings.rate_limit_per_minute
        self._user_timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        user = getattr(event.from_user, "id", None) or getattr(event.chat, "id", None)
        if not user:
            return await handler(event, data)
        now = time()
        timestamps = self._user_timestamps[user]
        # Remove old entries (older than 1 minute)
        timestamps[:] = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= self.rate_limit:
            # Skip handler, user is throttled
            return
        timestamps.append(now)
        return await handler(event, data)
