"""APScheduler — habit reminders, timezone-aware."""

import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

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
    """Send habit reminders — timezone-aware, runs every minute."""
    from app.core.database import get_session_maker
    from app.repositories.habit_repo import HabitRepository

    try:
        sm = get_session_maker()
        async with sm() as session:
            habit_repo = HabitRepository(session)
            items = await habit_repo.get_all_for_reminders()
        for habit, user, days, times in items:
            tz_name = getattr(user, "timezone", None) or "UTC"
            tz = ZoneInfo(tz_name)
            now_dt = datetime.now(tz)
            today_weekday = now_dt.weekday()
            now_hour, now_min = now_dt.hour, now_dt.minute
            if today_weekday not in days:
                continue
            for tt in times:
                if tt.hour == now_hour and tt.minute == now_min:
                    try:
                        from app.i18n.loader import get_texts
                        lang = getattr(user, "language", None) or "en"
                        texts = get_texts(lang)
                        msg = texts.get("reminder", "⏰ Time for: {habit_name}").format(habit_name=habit.title)
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=msg,
                        )
                    except Exception as e:
                        logger.warning("Reminder failed: %s", e)
    except Exception as e:
        logger.exception("Reminders job error: %s", e)


def setup_scheduler(bot) -> None:
    sched = get_scheduler()
    sched.add_job(run_reminders, IntervalTrigger(minutes=1), args=(bot,), id="habit_reminders")
    sched.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
