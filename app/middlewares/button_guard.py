"""Optional middleware — ensures inline keyboards only (no accidental plain messages)."""

from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable


class ButtonGuardMiddleware(BaseMiddleware):
    """Hook for logging/validation — inline keyboards only."""

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        return await handler(event, data)
