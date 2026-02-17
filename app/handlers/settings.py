"""Settings — language, timezone."""

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu, settings_menu, lang_select, timezone_full_keyboard, timezone_keyboard
from app.services import achievement_service, user_service, timezone_service
from app.texts import t

logger = logging.getLogger(__name__)
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
    tz = (cb.data.split(":", 1)[1] if ":" in (cb.data or "") else "UTC").strip()
    tid = cb.from_user.id if cb.from_user else 0

    if not timezone_service.validate_timezone(tz):
        await cb.answer(t("ru", "tz_invalid"), show_alert=True)
        return

    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User

        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            await cb.answer()
            return
        await user_service.update_timezone(session, user, tz)
        await session.commit()
        await achievement_service.check_achievements(
            session, user.id, user, cb.bot, user.telegram_id, trigger="profile_updated"
        )
        await session.commit()
        await session.refresh(user)

        # Hard debug: confirm DB save
        result = await session.execute(select(User.timezone).where(User.id == user.id))
        saved_tz = result.scalar_one()
        logger.info("DB CONFIRM timezone=%s user_id=%s", saved_tz, user.id)

        lang = user.language_code
        current_tz = (user.timezone or "UTC").strip()

    chat_id = cb.message.chat.id if cb.message else 0
    if not chat_id:
        await cb.answer()
        return

    # Delete old timezone screen (avoids edit_text on stale message)
    try:
        await cb.message.delete()
    except Exception:
        pass

    await cb.answer(t(lang, "tz_updated"), show_alert=True)

    # Confirmation message
    await cb.bot.send_message(chat_id, t(lang, "tz_confirmation_message", tz=current_tz))

    # Fresh timezone screen
    await cb.bot.send_message(
        chat_id,
        t(lang, "tz_prompt"),
        reply_markup=timezone_keyboard(current_tz, lang),
    )


@router.callback_query(lambda c: c.data == "settings_lang")
async def cb_settings_lang(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "lang_prompt"), reply_markup=lang_select(next_step="done", lang=lang, back_callback="settings"))


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
