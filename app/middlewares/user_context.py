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
        else:
            from_user = None
        if not from_user:
            return await handler(event, data)

        ref_telegram_id = None
        if isinstance(event, Message) and event.text and event.text.startswith("/start "):
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip().startswith("ref_"):
                try:
                    ref_telegram_id = int(parts[1][4:].strip())
                except ValueError:
                    pass

        try:
            session_factory = get_session_maker()
            async with session_factory() as session:
                user_repo = UserRepository(session)
                user_svc = UserService(user_repo)
                user: Any = None
                referral_notify: tuple[int, str] | None = None

                try:
                    existing_user = await user_repo.get_by_telegram_id(from_user.id)
                    if existing_user:
                        user = existing_user
                        data["user_just_created"] = False
                    elif ref_telegram_id is not None:
                        ref_repo = ReferralRepository(session)
                        ref_svc = ReferralService(ref_repo, user_repo)
                        try:
                            result = await ref_svc.process_referral(
                                session,
                                inviter_tg_id=ref_telegram_id,
                                new_user_tg_id=from_user.id,
                                username=from_user.username,
                                first_name=from_user.first_name or "",
                            )
                            if result.success and result.new_user:
                                user = result.new_user
                                data["user_just_created"] = True
                                if result.inviter_telegram_id is not None:
                                    referral_notify = (result.inviter_telegram_id, result.inviter_lang or "en")
                            else:
                                user, created = await user_svc.get_or_create(
                                    telegram_id=from_user.id,
                                    username=from_user.username,
                                    first_name=from_user.first_name or "",
                                    language=None,
                                    invited_by_id=None,
                                )
                                data["user_just_created"] = created
                        except Exception as ref_err:
                            logger.warning("Referral process failed, creating user without referral: %s", ref_err)
                            await session.rollback()
                            user, created = await user_svc.get_or_create(
                                telegram_id=from_user.id,
                                username=from_user.username,
                                first_name=from_user.first_name or "",
                                language=None,
                                invited_by_id=None,
                            )
                            data["user_just_created"] = created
                    else:
                        user, created = await user_svc.get_or_create(
                            telegram_id=from_user.id,
                            username=from_user.username,
                            first_name=from_user.first_name or "",
                            language=None,
                            invited_by_id=None,
                        )
                        data["user_just_created"] = created

                    data["user"] = user
                except Exception as load_err:
                    logger.exception("User load failed: %s", load_err)
                    if isinstance(event, Message):
                        await event.answer("⚠️ Temporary issue. Please try again in a moment.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⚠️ Temporary issue. Please try again.", show_alert=True)
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
                        msg = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get("referral_success", "🎉 +7 days subscription!")
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
