"""User context middleware — inject user and session."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, TelegramObject

from app.db import get_session_maker
from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository
from app.services.referral_service import ReferralService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


def _extract_referral_id(event: TelegramObject) -> int | None:
    """Extract referral telegram_id from /start command if present."""
    if not isinstance(event, Message) or not event.text:
        return None
    if not event.text.startswith("/start "):
        return None
    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if not payload.startswith("ref_"):
        return None

    # Support both signed (ref_{id}_{sig}) and legacy (ref_{id}) formats
    from app.utils.referral_token import verify_referral_code
    return verify_referral_code(payload)


async def _get_or_create_user(session, user_svc, from_user, ref_telegram_id):
    """Get existing user or create new one, handling referrals. Returns (user, created, referral_notify)."""
    user_repo = UserRepository(session) if not hasattr(user_svc, '_repo') else user_svc._repo
    referral_notify = None

    # Check if user exists
    existing_user = await user_svc._repo.get_by_telegram_id(from_user.id) if hasattr(user_svc, '_repo') else await session.execute(
        __import__('sqlalchemy', fromlist=['select']).select(
            __import__('app.models', fromlist=['User']).User
        ).where(
            __import__('app.models', fromlist=['User']).User.telegram_id == from_user.id
        )
    )

    # Simpler approach: just use the user_repo directly
    from sqlalchemy import select
    from app.models import User
    result = await session.execute(select(User).where(User.telegram_id == from_user.id))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return existing_user, False, None

    # New user — try referral flow
    if ref_telegram_id is not None:
        ref_repo = ReferralRepository(session)
        ref_svc = ReferralService(ref_repo, UserRepository(session))
        try:
            result = await ref_svc.process_referral(
                session,
                inviter_tg_id=ref_telegram_id,
                new_user_tg_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name or "",
            )
            if result.success and result.new_user:
                if result.inviter_telegram_id is not None:
                    referral_notify = (result.inviter_telegram_id, result.inviter_lang or "en")
                return result.new_user, True, referral_notify
        except Exception as ref_err:
            logger.warning("Referral process failed: %s", ref_err)
            await session.rollback()

    # Fallback: create user without referral
    user, created = await user_svc.get_or_create(
        telegram_id=from_user.id,
        username=from_user.username,
        first_name=from_user.first_name or "",
        language=None,
        invited_by_id=None,
    )
    return user, created, None


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = None
        if isinstance(event, (Message, CallbackQuery, PreCheckoutQuery)):
            from_user = getattr(event, "from_user", None)
        if not from_user:
            return await handler(event, data)

        ref_telegram_id = _extract_referral_id(event)

        try:
            session_factory = get_session_maker()
            async with session_factory() as session:
                user_repo = UserRepository(session)
                user_svc = UserService(user_repo)

                try:
                    user, created, referral_notify = await _get_or_create_user(
                        session, user_svc, from_user, ref_telegram_id
                    )
                    data["user"] = user
                    data["user_just_created"] = created
                except Exception as load_err:
                    logger.exception("User load failed: %s", load_err)
                    if isinstance(event, Message):
                        await event.answer("Temporary issue. Please try again in a moment.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("Temporary issue. Please try again.", show_alert=True)
                    return

                data["session"] = session
                data["user_service"] = user_svc
                data["referral_notify"] = referral_notify

                bot = None
                if isinstance(event, Message) and hasattr(event, "bot"):
                    bot = event.bot
                elif isinstance(event, CallbackQuery) and event.message:
                    bot = event.message.bot
                data["_referral_bot"] = bot

                try:
                    result = await handler(event, data)
                    await session.commit()
                    if referral_notify and data.get("_referral_bot"):
                        inviter_tg_id, lang = referral_notify
                        from app.utils.i18n import TRANSLATIONS
                        lang = lang if lang in ("ru", "en", "ar") else "ru"
                        msg = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get("referral_success", "+7 days subscription!")
                        try:
                            await data["_referral_bot"].send_message(chat_id=inviter_tg_id, text=msg)
                        except Exception as e:
                            logger.warning("Referral notification failed inviter=%s err=%s", inviter_tg_id, e)
                    return result
                except Exception:
                    await session.rollback()
                    raise
        except Exception as e:
            logger.exception("User load failed: %s", e)
            if isinstance(event, Message):
                await event.answer("Service temporarily unavailable. Please try again later.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Service temporarily unavailable.", show_alert=True)
            return
