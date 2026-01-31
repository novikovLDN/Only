"""
User context middleware — inject user and session into handler data.
"""

import logging

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.exc import ProgrammingError

from app.models.base import get_async_session_maker
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

try:
    import asyncpg
    _ASYNCPG_EXC = (asyncpg.exceptions.UndefinedColumnError, asyncpg.exceptions.PostgresError)
except ImportError:
    _ASYNCPG_EXC = ()


def _is_schema_error(exc: BaseException) -> bool:
    """Check if error indicates DB schema mismatch (missing column, etc)."""
    if isinstance(exc, _ASYNCPG_EXC) and "column" in str(exc).lower():
        return True
    msg = str(exc).lower()
    if "undefinedcolumn" in msg or "does not exist" in msg or ("column" in msg and "exist" in msg):
        return True
    if hasattr(exc, "__cause__") and exc.__cause__:
        return _is_schema_error(exc.__cause__)
    return False


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
                        "DB schema mismatch: model expects columns missing in DB. "
                        "Run: alembic upgrade head. Error: %s",
                        e,
                        exc_info=True,
                    )
                raise
