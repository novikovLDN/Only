"""Logging middleware."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        logger.info("Update: %s from user %s", type(event).__name__, user_id)
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception("Handler error: %s", e)
            raise
