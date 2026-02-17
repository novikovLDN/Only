"""Start and onboarding — lang, tz, referral."""

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import get_session_maker
from app.keyboards import lang_select, main_menu, tz_select
from app.services import achievement_service, referral_service, user_service
from app.texts import t
from app.utils.safe_edit import safe_edit_or_send

logger = logging.getLogger(__name__)

router = Router(name="start")


def _lang_from_callback(data: str) -> str:
    return "ru" if "ru" in (data or "") else "en"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    logger.info("START handler triggered tid=%s", message.from_user.id if message.from_user else 0)
    tid = message.from_user.id if message.from_user else 0
    uname = message.from_user.username if message.from_user else None
    fname = message.from_user.first_name or ""
    tlang = message.from_user.language_code if message.from_user else None

    ref_id = None
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            ref_id = int(parts[1][4:])
        except ValueError:
            pass

    sm = get_session_maker()
    async with sm() as session:
        user, created = await user_service.get_or_create(
            session, tid, uname, fname, telegram_language_code=tlang
        )
        ref = None
        if ref_id and ref_id != user.id:
            ref = await referral_service.create_referral(session, ref_id, user.id)
        await session.commit()
        if ref:
            from app.models import User
            referrer = await session.get(User, ref_id)
            if referrer:
                await achievement_service.check_achievements(
                    session, referrer.id, referrer, message.bot, referrer.telegram_id, trigger="friend_invited"
                )
                await session.commit()
        if not created:
            await achievement_service.check_achievements(
                session, user.id, user, message.bot, user.telegram_id, trigger="user_returns"
            )
            await session.commit()
        lang = user.language_code
        is_premium = user_service.is_premium(user)
        if created or user.language_code not in ("ru", "en"):
            await message.answer(t("ru", "lang_prompt"), reply_markup=lang_select(next_step="tz"))
            return
    await message.answer(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("lang_") and "_tz" in (c.data or ""))
async def cb_lang_onboard(cb: CallbackQuery) -> None:
    await cb.answer()
    lang = _lang_from_callback(cb.data or "")
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await user_service.update_language(session, user, lang)
        await session.commit()
        if user:
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="profile_updated"
            )
            await session.commit()

    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=tz_select(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("tz_onboard:"))
async def cb_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tz = (cb.data or "").split(":", 1)[1] if ":" in (cb.data or "") else "Europe/Moscow"
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""

    from app.services import timezone_service
    if not timezone_service.validate_timezone(tz):
        tz = "Europe/Moscow"
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await user_service.update_timezone(session, user, tz)
        await session.commit()
        if user:
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="profile_updated"
            )
            await session.commit()
        lang = user.language_code if user else "en"
        is_premium = user_service.is_premium(user) if user else False

    await cb.message.edit_text(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(lambda c: c.data == "back_main")
async def cb_back_main(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        is_premium = user_service.is_premium(user) if user else False

    await safe_edit_or_send(
        cb,
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )
