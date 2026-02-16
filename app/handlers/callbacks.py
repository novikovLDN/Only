"""Shared callbacks — back_main, lang, tz (from settings)."""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db import get_session_maker
from app.keyboards import main_menu
from app.models import User
from app.services import users
from app.texts import t

router = Router(name="callbacks")


@router.callback_query(lambda c: c.data == "back_main")
async def cb_back_main(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.clear()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and "lang_" in (c.data or "") and "_main" in (c.data or ""))
async def cb_lang(cb: CallbackQuery) -> None:
    await cb.answer()
    lang = "ru" if "lang_ru" in (cb.data or "") else "en"
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await users.update_language(session, user, lang)
        await session.commit()

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("tz_") and c.data != "tz_other")
async def cb_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tz = cb.data.replace("tz_", "")
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await users.update_timezone(session, user, tz)
        await session.commit()
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))
