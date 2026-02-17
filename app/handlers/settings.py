"""Settings — language, timezone."""

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu, settings_menu, lang_select, timezone_full_keyboard, timezone_keyboard
from app.services import achievement_service, user_service
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
        current_tz = user.timezone if user else "UTC"

    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=timezone_keyboard(current_tz, lang))


@router.callback_query(lambda c: c.data == "tz_other")
async def cb_tz_other(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        current_tz = user.timezone if user else "UTC"

    await cb.message.edit_text(
        t(lang, "tz_full_prompt"),
        reply_markup=timezone_full_keyboard(current_tz, 0, lang),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("tz_page:"))
async def cb_tz_page(cb: CallbackQuery) -> None:
    await cb.answer()
    try:
        page = int(cb.data.split(":")[1])
    except (ValueError, IndexError):
        page = 0
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        current_tz = user.timezone if user else "UTC"

    await cb.message.edit_text(
        t(lang, "tz_full_prompt"),
        reply_markup=timezone_full_keyboard(current_tz, page, lang),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("tz_set:"))
async def cb_tz_set(cb: CallbackQuery) -> None:
    tz = cb.data.split(":", 1)[1] if ":" in (cb.data or "") else "UTC"
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if user:
            await user_service.update_timezone(session, user, tz)
        await session.commit()
        if user:
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="profile_updated"
            )
            await session.commit()
        lang = user.language_code if user else "en"
        current_tz = user.timezone if user else "UTC"

    await cb.answer(t(lang, "tz_updated"))
    await cb.message.edit_text(t(lang, "tz_prompt"), reply_markup=timezone_keyboard(current_tz, lang))


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
        if user:
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="profile_updated"
            )
            await session.commit()

    confirm_key = "lang_updated_ru" if lang == "ru" else "lang_updated_en"
    await cb.message.edit_text(t(lang, confirm_key), reply_markup=settings_menu(lang))
