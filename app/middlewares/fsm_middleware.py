"""
FSM middleware — timeout и защита от stale states.

При /start — сброс FSM (пользователь не застревает).
Timeout реализуется через FSM storage TTL (Redis) или периодическую проверку.
Для MemoryStorage — простой clear при /start.
"""

import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)

# Ключ в FSM data для времени последней активности
FSM_LAST_ACTIVITY = "fsm_last_activity"


class FSMTimeoutMiddleware(BaseMiddleware):
    """
    Обновляет timestamp последней активности в FSM data.
    Для Redis storage можно добавить TTL на key.
    MemoryStorage не поддерживает TTL — timeout обрабатывается в handler /start.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state = data.get("state")
        if state:
            try:
                await state.update_data(**{FSM_LAST_ACTIVITY: time.time()})
            except Exception:
                pass
        return await handler(event, data)
