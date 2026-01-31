"""
Global error handler — severity classification, admin alerts.

🟥 CRITICAL → admin alert immediately
🟧 WARNING → logged, admin on cooldown
🟩 OK → silent log
"""

import logging
from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import ErrorEvent

from app.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = 6214188086


def _severity(exc: BaseException) -> str:
    """Classify error severity."""
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__.lower()
    if any(x in exc_str + exc_type for x in [
        "undefinedcolumn", "does not exist", "schema", "migration",
        "programmingerror", "operationalerror", "connection"
    ]):
        return "critical"
    if any(x in exc_str + exc_type for x in [
        "timeout", "retry", "forbidden", "unauthorized", "conflict"
    ]):
        return "warning"
    return "ok"


def _get_bot_from_event(event: ErrorEvent):
    """Extract bot from ErrorEvent or core.bot_instance."""
    try:
        update = event.update
        if hasattr(update, "message") and update.message:
            b = getattr(update.message, "bot", None)
            if b:
                return b
        if hasattr(update, "callback_query") and update.callback_query:
            b = getattr(update.callback_query, "bot", None)
            if b:
                return b
    except Exception:
        pass
    from app.core.bot_instance import get_bot
    return get_bot()


router = Router(name="errors")


def _get_chat_id_from_event(event: ErrorEvent) -> int | None:
    """Extract chat_id for user-facing error reply."""
    try:
        update = event.update
        if hasattr(update, "message") and update.message:
            return update.message.chat.id if update.message.chat else None
        if hasattr(update, "callback_query") and update.callback_query:
            msg = update.callback_query.message
            return msg.chat.id if msg and msg.chat else None
    except Exception:
        pass
    return None


@router.error()
async def global_error_handler(event: ErrorEvent) -> None:
    """Catch all errors. Log, classify, alert on critical/warning."""
    exc = event.exception
    severity = _severity(exc)
    logger.error("Handler error: %s", exc, exc_info=(severity == "critical"))

    # Schema degraded: session is None, handler failed — reply to user
    if isinstance(exc, (AttributeError, TypeError)) and "NoneType" in str(exc):
        bot = _get_bot_from_event(event)
        chat_id = _get_chat_id_from_event(event)
        if bot and chat_id:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Система обновляется, попробуйте через минуту.",
                )
            except Exception:
                pass

    if severity == "critical":
        logger.critical("CRITICAL error: %s", exc, exc_info=True)
        try:
            bot = _get_bot_from_event(event)
            if bot:
                chat_id = getattr(settings, "alert_chat_id_int", None) or settings.alert_chat_id or ADMIN_CHAT_ID
                aid = int(chat_id) if chat_id else ADMIN_CHAT_ID
                await bot.send_message(
                    chat_id=aid,
                    text=f"🚨 [CRITICAL] Bot Error\n{str(exc)[:400]}",
                )
        except Exception as ae:
            logger.warning("Could not send admin alert: %s", ae)
