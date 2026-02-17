"""i18n middleware — strict language from user.language, no fallback guessing."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.utils.i18n import get_presets, get_weekdays, t as i18n_t

logger = logging.getLogger(__name__)

VALID_LANGUAGES = frozenset(("ru", "en", "ar"))


def _resolve_lang(user: Any) -> str:
    """user.language or user.language_code is source of truth. Invalid → 'ru' + log."""
    if not user:
        return "ru"
    raw = getattr(user, "language", None) or getattr(user, "language_code", None)
    if raw in VALID_LANGUAGES:
        return raw
    if raw is not None and raw not in VALID_LANGUAGES:
        logger.critical("Invalid user language=%r, forcing 'ru'", raw)
    return "ru"


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        lang = _resolve_lang(user)
        data["lang"] = lang

        def _t(key: str, **kw) -> str:
            return i18n_t(lang, key, **kw)

        data["t"] = _t
        data["presets"] = get_presets(lang)
        data["weekdays_labels"] = get_weekdays(lang)
        return await handler(event, data)
