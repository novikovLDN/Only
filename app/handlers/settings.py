"""Settings."""

from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db import get_session_maker
from app.keyboards import lang_select, main_menu, settings_menu, tz_select
from app.models import User
from app.services import users
from app.texts import t

router = Router(name="settings")


@router.callback_query(lambda c: c.data == "settings")
async def cb_settings(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "btn_settings"), reply_markup=settings_menu(lang))


@router.callback_query(lambda c: c.data == "settings_lang")
async def cb_settings_lang(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "lang_prompt"), reply_markup=lang_select(next_step="main"))


@router.callback_query(lambda c: c.data == "settings_tz")
async def cb_settings_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=tz_select(lang))
