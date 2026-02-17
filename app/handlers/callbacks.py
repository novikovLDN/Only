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
    d = cb.data or ""
    lang = "ar" if "lang_ar" in d else ("en" if "lang_en" in d else "ru")
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await users.update_language(session, user, lang)
        await session.commit()

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("tz_onboard:"))
async def cb_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tz = (cb.data or "").split(":", 1)[1] if ":" in (cb.data or "") else "Europe/Moscow"
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            from app.services import user_service
            await user_service.update_timezone(session, user, tz)
        await session.commit()
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))
