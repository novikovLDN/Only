"""APScheduler — habit reminders every 60s, habit_time + timezone; daily metrics recalc."""

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import get_session_maker
from app.keyboards.reminder import reminder_buttons
from app.texts import _normalize_lang, t
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
    """Every 60s: fresh DB fetch, timezone-aware conversion, direct weekday+time match.
    No caching — DB is single source of truth."""
    try:
        now_utc = datetime.now(timezone.utc)
        sm = get_session_maker()
        async with sm() as s:
            result = await s.execute(
                select(HabitTime, Habit, User)
                .join(Habit, HabitTime.habit_id == Habit.id)
                .join(User, Habit.user_id == User.id)
                .where(Habit.is_active == True)
            )
            rows = result.all()

        for ht, habit, user in rows:
            try:
                user_tz = ZoneInfo(user.timezone or "Europe/Moscow")
            except Exception:
                user_tz = ZoneInfo("Europe/Moscow")

            now_local = now_utc.astimezone(user_tz)
            logger.debug(
                "TZ DEBUG: user_id=%s tz=%s now_local=%s",
                user.id, user.timezone, now_local,
            )
            weekday = now_local.weekday()
            current_time = now_local.time().replace(second=0, microsecond=0)
            today = now_local.date()

            if ht.weekday != weekday or ht.time != current_time:
                continue

            async with sm() as session:
                if await habit_log_service.has_log_today(session, user.id, habit.id, today):
                    continue

                lang = _normalize_lang(user.language_code)
                await rem_svc.reset_usage_if_needed(session, user.id, lang)
                used = await rem_svc.get_used_indices(session, user.id)
                phrase, idx = rem_svc.get_phrase(lang, used)
                await rem_svc.record_phrase_usage(session, user.id, habit.id, idx)
                await session.commit()

            try:
                time_str = ht.time.strftime("%H:%M") if hasattr(ht.time, "strftime") else str(ht.time)
                text = t(lang, "notification_format", title=habit.title, time=time_str)
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=reminder_buttons(habit.id, lang),
                )
            except Exception as e:
                logger.warning("Reminder send failed user=%s habit=%s: %s", user.telegram_id, habit.id, e)

    except Exception as e:
        logger.exception("Reminders job error: %s", e)


async def run_daily_metrics_recalc(bot) -> None:
    """Daily 00:05 UTC: recalc user_metrics for all users."""
    try:
        from app.services import metrics_service
        sm = get_session_maker()
        async with sm() as session:
            await metrics_service.recalculate_all_metrics(session, bot)
            await session.commit()
        logger.info("Daily metrics recalc completed")
    except Exception as e:
        logger.exception("Daily metrics recalc failed: %s", e)


def setup_scheduler(bot) -> None:
    sched = get_scheduler()
    sched.add_job(
        run_reminders,
        trigger="interval",
        minutes=1,
        args=(bot,),
        id="habit_reminders",
        replace_existing=True,
    )
    sched.add_job(
        run_daily_metrics_recalc,
        trigger=CronTrigger(hour=0, minute=5),
        args=(bot,),
        id="daily_metrics_recalc",
        replace_existing=True,
    )
    sched.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
