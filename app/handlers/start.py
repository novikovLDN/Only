"""Start and onboarding."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.db import get_session_maker
from app.keyboards import lang_select, main_menu, tz_select
from app.services import users
from app.texts import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tid = message.from_user.id if message.from_user else 0
    uname = message.from_user.username if message.from_user else None
    fname = message.from_user.first_name if message.from_user else None

    sm = get_session_maker()
    async with sm() as session:
        user, created = await users.get_or_create(session, tid, uname, fname)
        await session.commit()
        lang = user.language_code
        if created or user.language_code not in ("ru", "en"):
            await message.answer(t("ru", "lang_prompt"), reply_markup=lang_select(next_step="tz"))
            return
        await message.answer(t(lang, "main_title"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("lang_") and "_tz" in (c.data or ""))
async def cb_lang_onboard(cb: CallbackQuery) -> None:
    await cb.answer()
    lang = "ru" if "lang_ru" in (cb.data or "") else "en"
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid)
        user = r.scalar_one_or_none()
        if user:
            await users.update_language(session, user, lang)
        await session.commit()

    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=tz_select(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("tz_") and c.data != "tz_other")
async def cb_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tz = cb.data.replace("tz_", "")
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid)
        user = r.scalar_one_or_none()
        if user:
            await users.update_timezone(session, user, tz)
        await session.commit()
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))
