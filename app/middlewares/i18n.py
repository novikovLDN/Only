"""i18n middleware — inject language and t() into handlers."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.utils.i18n import get_presets, get_weekdays, t as i18n_t


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        lang = "en"
        if user and hasattr(user, "language") and getattr(user, "language", None) in ("ru", "en"):
            lang = user.language
        data["lang"] = lang

        def _t(key: str, **kw) -> str:
            return i18n_t(lang, key, **kw)

        data["t"] = _t
        data["presets"] = get_presets(lang)
        data["weekdays_labels"] = get_weekdays(lang)
        return await handler(event, data)
