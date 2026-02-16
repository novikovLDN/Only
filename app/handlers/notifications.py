"""Notification callbacks — Done / Skip from reminders."""

from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards.reminder import reminder_buttons, skip_reasons
from app.services import habit_log_service, reminders as rem_svc
from app.services import user_service
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
        if await habit_log_service.has_log_today(session, user.id, habit_id, date.today()):
            return
        lang = user.language_code if user.language_code in ("ru", "en") else "ru"
        await rem_svc.reset_usage_if_needed(session, user.id, lang)
        used = await rem_svc.get_used_indices(session, user.id)
        phrase, idx = rem_svc.get_phrase(lang, used)
        await habit_log_service.log_done(session, habit_id, user.id, date.today())
        await rem_svc.record_phrase_usage(session, user.id, idx)
        await session.commit()

    await cb.message.edit_text("🎉")
    await cb.message.answer(phrase)


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
        await habit_log_service.log_skipped(session, habit_id, user.id, date.today())
        await session.commit()
        lang = user.language_code

    await cb.message.edit_text(t(lang, "reminder_skip_msg"))


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
