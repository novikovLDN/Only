"""Snooze reminder handler — reschedule reminder after 15/30 min."""

import asyncio
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards.reminder import reminder_buttons
from app.services import user_service
from app.texts import t

logger = logging.getLogger(__name__)

router = Router(name="snooze")


@router.callback_query(F.data.startswith("snooze:"))
async def cb_snooze(cb: CallbackQuery) -> None:
    """Snooze a reminder for 15 or 30 minutes."""
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) < 3:
        return
    habit_id = int(parts[1])
    minutes = int(parts[2])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"

    # Acknowledge snooze
    try:
        await cb.message.edit_text(
            t(lang, "snooze_confirmed", minutes=minutes),
        )
    except Exception:
        pass

    # Schedule re-send after delay
    async def _resend():
        await asyncio.sleep(minutes * 60)
        try:
            from app.services import habit_service
            async with sm() as session:
                habit = await habit_service.get_by_id(session, habit_id)
                if not habit:
                    return
                title = habit.title

            await cb.bot.send_message(
                chat_id=tid,
                text=t(lang, "snooze_reminder", title=title),
                reply_markup=reminder_buttons(habit_id, lang),
            )
        except Exception as e:
            logger.warning("Snooze re-send failed user=%s: %s", tid, e)

    asyncio.create_task(_resend())
