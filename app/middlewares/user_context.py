"""User context middleware — inject user and session."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.core.database import get_session_maker
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = None
        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user
        if not from_user:
            return await handler(event, data)

        ref_telegram_id = None
        if isinstance(event, Message) and event.text and event.text.startswith("/start "):
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1 and parts[1].startswith("ref_"):
                try:
                    ref_telegram_id = int(parts[1][4:].strip())
                except ValueError:
                    pass

        session_factory = get_session_maker()
        async with session_factory() as session:
            user_repo = UserRepository(session)
            user_svc = UserService(user_repo)
            inviter = await user_repo.get_by_telegram_id(ref_telegram_id) if ref_telegram_id else None
            invited_by_id = inviter.id if inviter else None
            user, created = await user_svc.get_or_create(
                telegram_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name or "",
                language=from_user.language_code or "en",
                invited_by_id=invited_by_id,
            )
            if inviter and created and inviter.id != user.id:
                from app.repositories.referral_repo import ReferralRepository
                from app.services.referral_service import ReferralService
                ref_repo = ReferralRepository(session)
                ref_svc = ReferralService(ref_repo, user_repo)
                await ref_svc.apply_referral(user, inviter.id)
            data["user"] = user
            data["session"] = session
            data["user_service"] = user_svc
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
