"""APScheduler — habit reminders every 60s, timezone-aware."""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.db import get_session_maker
from app.keyboards.reminder import reminder_buttons
from app.models import Habit, User
from app.services import reminders as rem_svc

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            job_defaults={"coalesce": True, "max_instances": 1},
        )
    return _scheduler


async def run_reminders(bot) -> None:
    """Every 60s: for each habit, if user's local time matches remind_time and no log today → send reminder."""
    try:
        sm = get_session_maker()
        async with sm() as s:
            result = await s.execute(
                select(Habit, User).join(User, Habit.user_id == User.id).where(Habit.is_active == True)
            )
            rows = result.all()

        tz_cache = {}
        for habit, user in rows:
            tz_name = user.timezone or "UTC"
            try:
                tz = tz_cache.get(tz_name) or ZoneInfo(tz_name)
                tz_cache[tz_name] = tz
            except Exception:
                tz = ZoneInfo("UTC")

            now_dt = datetime.now(tz)
            today = now_dt.date()
            now_hour, now_min = now_dt.hour, now_dt.minute
            rt = habit.remind_time
            if rt.hour != now_hour or rt.minute != now_min:
                continue

            async with sm() as session:
                if await rem_svc.has_log_today(session, user.id, habit.id, today):
                    continue

                lang = user.language_code if user.language_code in ("ru", "en") else "ru"
                await rem_svc.reset_usage_if_needed(session, user.id, lang)
                used = await rem_svc.get_used_indices(session, user.id)
                phrase, idx = rem_svc.get_phrase(lang, used)
                await rem_svc.record_phrase_usage(session, user.id, idx)
                await session.commit()

            try:
                text = f"🟢 {habit.title}\n\n{phrase}"
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=reminder_buttons(habit.id, lang),
                )
            except Exception as e:
                logger.warning("Reminder send failed user=%s habit=%s: %s", user.telegram_id, habit.id, e)

    except Exception as e:
        logger.exception("Reminders job error: %s", e)


def setup_scheduler(bot) -> None:
    sched = get_scheduler()
    sched.add_job(run_reminders, IntervalTrigger(seconds=60), args=(bot,), id="habit_reminders")
    sched.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
