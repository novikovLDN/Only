"""i18n middleware — inject language and t() into handlers."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.i18n.loader import get_texts, get_presets, get_weekdays


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        lang = "en"
        if user and hasattr(user, "language"):
            lang = getattr(user, "language", "en") or "en"
        data["lang"] = lang
        data["t"] = lambda key, **kw: get_texts(lang).get(key, key).format(**kw) if kw else get_texts(lang).get(key, key)
        data["presets"] = get_presets(lang)
        data["weekdays_labels"] = get_weekdays(lang)
        return await handler(event, data)
