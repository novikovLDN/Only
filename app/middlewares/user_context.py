"""
User context middleware — inject user and session into handler data.

On schema error: minimal in-memory user, no DB, continue update pipeline.
Middleware must NEVER kill update pipeline.
"""

import logging
from types import SimpleNamespace

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.exc import ProgrammingError

from app.config import settings
from app.models.base import get_async_session_maker
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

try:
    import asyncpg
    _ASYNCPG_EXC = (asyncpg.exceptions.UndefinedColumnError,)
except ImportError:
    _ASYNCPG_EXC = ()

SCHEMA_ERROR_USER_MESSAGE = "⚠️ Система обновляется, попробуйте через минуту."


def _minimal_user_context(from_user) -> SimpleNamespace:
    """Fallback in-memory user when DB schema mismatch. Skip DB access."""
    return SimpleNamespace(
        id=from_user.id,
        telegram_id=from_user.id,
        username=from_user.username,
        first_name=from_user.first_name or "",
        last_name=from_user.last_name,
        language_code=from_user.language_code or "en",
        referral_code=None,
        tier="free",
        is_blocked=False,
        timezone="UTC",
        notifications_enabled=True,
    )


def _is_schema_error(exc: BaseException) -> bool:
    """Check if error indicates DB schema mismatch (missing column, etc)."""
    if isinstance(exc, _ASYNCPG_EXC):
        return True
    msg = str(exc).lower()
    if "undefinedcolumn" in msg or "does not exist" in msg or ("column" in msg and "exist" in msg):
        return True
    if hasattr(exc, "__cause__") and exc.__cause__:
        return _is_schema_error(exc.__cause__)
    return False


async def _send_schema_error_alert(bot: Bot, exc: BaseException) -> None:
    """Send CRITICAL alert to admin."""
    chat_id = getattr(settings, "alert_chat_id_int", None) or settings.alert_chat_id
    try:
        aid = int(chat_id) if chat_id else 6214188086
        text = (
            f"🚨 [CRITICAL] DB Schema Mismatch\n"
            f"Run: alembic upgrade head\n"
            f"Error: {str(exc)[:300]}"
        )
        await bot.send_message(chat_id=aid, text=text)
    except Exception as ae:
        logger.warning("Failed to send admin alert: %s", ae)


async def _reply_to_user(event: TelegramObject, text: str, bot: Bot) -> None:
    """Send user-facing message on schema error."""
    try:
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer()
            if event.message:
                await event.message.answer(text)
    except Exception as e:
        logger.warning("Failed to reply to user: %s", e)


class UserContextMiddleware(BaseMiddleware):
    """Inject db session and user into handler."""

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        from_user = None
        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user
        if not from_user:
            return await handler(event, data)
        referral_code = None
        if isinstance(event, Message) and event.text and event.text.startswith("/start "):
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1 and parts[1].startswith("ref_"):
                referral_code = parts[1][4:].strip()
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            try:
                user_svc = UserService(session)
                user, _ = await user_svc.get_or_create_user(
                    telegram_id=from_user.id,
                    username=from_user.username,
                    first_name=from_user.first_name or "",
                    last_name=from_user.last_name,
                    language_code=from_user.language_code or "en",
                )
                if referral_code:
                    from app.services.referral_service import ReferralService

                    ref_svc = ReferralService(session)
                    await ref_svc.apply_referral(user.id, referral_code)
                data["user"] = user
                data["session"] = session
                data["user_service"] = user_svc
                result = await handler(event, data)
                await session.commit()
                return result
            except (ProgrammingError, *_ASYNCPG_EXC, Exception) as e:
                await session.rollback()
                if _is_schema_error(e):
                    logger.critical(
                        "DB schema mismatch: using minimal user context. "
                        "Run: alembic upgrade head. Error: %s",
                        e,
                        exc_info=True,
                    )
                    from app.core.bot_instance import get_bot
                    bot = getattr(event, "bot", None) or data.get("bot") or get_bot()
                    if bot:
                        await _send_schema_error_alert(bot, e)
                    # Fail-safe: minimal in-memory user, no session, continue pipeline
                    data["user"] = _minimal_user_context(from_user)
                    data["session"] = None
                    data["user_service"] = None
                    data["schema_degraded"] = True
                    return await handler(event, data)
                raise
