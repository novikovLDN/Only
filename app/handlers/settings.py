"""Settings — language, timezone."""

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu, settings_menu, lang_select, tz_select
from app.services import user_service
from app.texts import t

router = Router(name="settings")


@router.callback_query(lambda c: c.data == "settings")
async def cb_settings(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "settings_menu"), reply_markup=settings_menu(lang))


@router.callback_query(lambda c: c.data == "settings_tz")
async def cb_settings_tz(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=tz_select(lang, prefix="settz_"))


@router.callback_query(lambda c: c.data and c.data.startswith("settz_") and c.data != "settz_other")
async def cb_settz_select(cb: CallbackQuery) -> None:
    await cb.answer()
    tz = (cb.data or "").replace("settz_", "")
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if user:
            await user_service.update_timezone(session, user, tz)
        await session.commit()
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "settings_menu"), reply_markup=settings_menu(lang))


@router.callback_query(lambda c: c.data == "settings_lang")
async def cb_settings_lang(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "lang_prompt"), reply_markup=lang_select(next_step="done"))


@router.callback_query(lambda c: c.data and c.data.startswith("lang_") and "_done" in (c.data or ""))
async def cb_lang_select(cb: CallbackQuery) -> None:
    await cb.answer()
    lang = "ru" if "ru" in (cb.data or "") else "en"
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

    confirm_key = "lang_updated_ru" if lang == "ru" else "lang_updated_en"
    await cb.message.edit_text(t(lang, confirm_key), reply_markup=settings_menu(lang))
