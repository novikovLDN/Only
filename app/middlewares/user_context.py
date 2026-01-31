"""
User context middleware — inject user and session into handler data.
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.models.base import get_async_session_maker
from app.services.user_service import UserService


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
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise
