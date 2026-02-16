"""APScheduler — habit reminders every 60s, habit_time + timezone."""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import get_session_maker
from app.keyboards.reminder import reminder_buttons
from app.models import Habit, HabitTime, User
from app.services import habit_log_service, reminders as rem_svc

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
    """Every 60s: habit_time JOIN habit JOIN user, match weekday+time in user TZ."""
    try:
        sm = get_session_maker()
        async with sm() as s:
            result = await s.execute(
                select(HabitTime, Habit, User)
                .join(Habit, HabitTime.habit_id == Habit.id)
                .join(User, Habit.user_id == User.id)
                .where(Habit.is_active == True)
            )
            rows = result.all()

        tz_cache = {}
        for ht, habit, user in rows:
            tz_name = user.timezone or "UTC"
            try:
                tz = tz_cache.get(tz_name) or ZoneInfo(tz_name)
                tz_cache[tz_name] = tz
            except Exception:
                tz = ZoneInfo("UTC")

            now_dt = datetime.now(tz)
            today = now_dt.date()
            weekday = (now_dt.weekday() + 1) % 7
            if weekday != ht.weekday:
                continue

            t_val = ht.time
            if hasattr(t_val, "hour"):
                h, m = t_val.hour, t_val.minute
            else:
                try:
                    parts = str(t_val).split(":")
                    h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    continue

            if now_dt.hour != h or now_dt.minute != m:
                continue

            async with sm() as session:
                if await habit_log_service.has_log_today(session, user.id, habit.id, today):
                    continue

                lang = user.language_code if user.language_code in ("ru", "en") else "ru"
                await rem_svc.reset_usage_if_needed(session, user.id, lang)
                used = await rem_svc.get_used_indices(session, user.id)
                phrase, idx = rem_svc.get_phrase(lang, used)
                await rem_svc.record_phrase_usage(session, user.id, habit.id, idx)
                await session.commit()

            try:
                from app.texts import t
                time_str = ht.time.strftime("%H:%M") if hasattr(ht.time, "strftime") else str(ht.time)
                text = t(lang, "notification_format").format(title=habit.title, time=time_str)
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
