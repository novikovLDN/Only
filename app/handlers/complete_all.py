"""Complete all habits handler — batch mark all pending habits as done."""

import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu
from app.services import achievement_service, habit_log_service, user_service, xp_service
from app.texts import t

logger = logging.getLogger(__name__)

router = Router(name="complete_all")


@router.callback_query(F.data.startswith("complete_all:"))
async def cb_complete_all(cb: CallbackQuery) -> None:
    """Complete all specified habits at once."""
    await cb.answer()
    ids_str = cb.data.split(":", 1)[1]
    habit_ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return

        today = date.today()
        completed = 0
        for habit_id in habit_ids:
            if await habit_log_service.has_log_today(session, user.id, habit_id, today):
                continue
            await habit_log_service.log_done(session, habit_id, user.id, today)
            await xp_service.add_xp(user, session, cb.bot)
            completed += 1

        if completed > 0:
            await session.commit()
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="habit_completed"
            )
            await session.commit()

        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
        is_premium = user_service.is_premium(user)
        fname = cb.from_user.first_name if cb.from_user else ""

    await cb.message.answer(
        t(lang, "complete_all_done", count=completed),
    )
    await cb.message.answer(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )
