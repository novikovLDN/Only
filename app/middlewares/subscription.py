"""Subscription guard middleware. Must run after UserContextMiddleware."""

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        is_premium = False
        if user is not None and hasattr(user, "subscription_until") and user.subscription_until is not None:
            is_premium = user.subscription_until > datetime.now(timezone.utc)
        data["is_premium"] = is_premium
        return await handler(event, data)
