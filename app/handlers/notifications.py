"""Notification callbacks — Done / Skip from reminders."""

import asyncio
from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu
from app.keyboards.reminder import reminder_buttons, skip_reasons
from app.services import achievement_service, habit_log_service, reminders as rem_svc, user_service, xp_service
from app.texts import t

router = Router(name="notifications")


@router.callback_query(F.data.startswith("habit_done:"))
async def cb_habit_done(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        today = date.today()
        if await habit_log_service.has_log_today(session, user.id, habit_id, today):
            return
        lang = user.language_code if user.language_code in ("ru", "en") else "ru"
        await rem_svc.reset_usage_if_needed(session, user.id, lang)
        used = await rem_svc.get_used_indices(session, user.id)
        _, idx = rem_svc.get_phrase(lang, used)
        await habit_log_service.log_done(session, habit_id, user.id, today)
        await rem_svc.record_phrase_usage(session, user.id, habit_id, idx)
        await session.refresh(user)
        await xp_service.add_xp(user, session, cb.bot)
        await achievement_service.check_achievements(
            session, user.id, user, cb.bot, user.telegram_id
        )
        await session.commit()
        is_premium = user_service.is_premium(user)
        fname = cb.from_user.first_name if cb.from_user else ""

    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.message.answer("🎉")
    await asyncio.sleep(3)
    await cb.message.answer(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(F.data.startswith("habit_skip:"))
async def cb_habit_skip(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code

    await cb.message.edit_text(
        t(lang, "skip_why"),
        reply_markup=skip_reasons(lang, habit_id),
    )


@router.callback_query(F.data.startswith("skip_reason:"))
async def cb_skip_reason(cb: CallbackQuery) -> None:
    await cb.answer()
    parts = cb.data.split(":")
    habit_id = int(parts[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        today = date.today()
        if await habit_log_service.has_log_today(session, user.id, habit_id, today):
            return
        await habit_log_service.log_skipped(session, habit_id, user.id, today)
        await session.commit()
        lang = user.language_code
        is_premium = user_service.is_premium(user)
        fname = cb.from_user.first_name if cb.from_user else ""

    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.message.answer(t(lang, "reminder_skip_msg"))
    await asyncio.sleep(3)
    await cb.message.answer(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(F.data.startswith("back_to_reminder:"))
async def cb_back_to_reminder(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        from app.services import habit_service
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit:
            return
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(
        f"🟢 {habit.title}",
        reply_markup=reminder_buttons(habit_id, lang),
    )
