"""Reminder callbacks — Done, Skip, Skip reason."""

from datetime import date

from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db import get_session_maker
from app.keyboards import main_menu, skip_reasons
from app.models import User
from app.services import reminders as rem_svc
from app.texts import t

router = Router(name="reminders")


@router.callback_query(lambda c: c.data and c.data.startswith("done_"))
async def cb_done(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split("_")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        today = date.today()
        if not await rem_svc.has_log_today(session, user.id, habit_id, today):
            await rem_svc.log_done(session, habit_id, user.id, today)
            await session.commit()
        lang = user.language_code

    await cb.message.edit_text("🎉", reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("skip_") and not (c.data or "").startswith("skip_reason_") and not (c.data or "").startswith("skip_back_"))
async def cb_skip(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split("_")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code

    await cb.message.edit_text(t(lang, "skip_why"), reply_markup=skip_reasons(lang, habit_id))


@router.callback_query(lambda c: c.data and c.data.startswith("skip_reason_"))
async def cb_skip_reason(cb: CallbackQuery) -> None:
    await cb.answer()
    parts = cb.data.split("_")
    habit_id = int(parts[2])
    reason = parts[3] if len(parts) > 3 else "—"
    tid = cb.from_user.id if cb.from_user else 0

    reason_map = {"tired": "😴 Tired", "sick": "🤒 Sick", "no_want": "🙅 Don't want"}
    skip_reason = reason_map.get(reason, reason)

    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        today = date.today()
        if not await rem_svc.has_log_today(session, user.id, habit_id, today):
            await rem_svc.log_skipped(session, habit_id, user.id, today, skip_reason)
            await session.commit()
        lang = user.language_code

    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("skip_back_"))
async def cb_skip_back(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "main_title"), reply_markup=main_menu(lang))
