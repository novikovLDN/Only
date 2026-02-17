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
    """Every 60s: habit_time JOIN habit JOIN user, match weekday+time in user TZ.
    Always fetches fresh from DB — no timezone caching."""
    try:
        now_utc = datetime.now(timezone.utc)  # timezone-aware, no naive datetime
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

            now_user = now_utc.astimezone(tz)
            today = now_user.date()
            if now_user.weekday() != ht.weekday:
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

            if now_user.hour != h or now_user.minute != m:
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


async def run_validate_timezones(bot) -> None:
    """Daily 00:15 UTC: fix users with invalid IANA timezones (reset to UTC)."""
    try:
        from zoneinfo import ZoneInfo
        from app.services import user_service
        sm = get_session_maker()
        async with sm() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
        fixed = 0
        for user in users:
            try:
                ZoneInfo(user.timezone or "UTC")
            except Exception:
                await user_service.update_user_timezone_by_id(user.id, "UTC")
                fixed += 1
        if fixed:
            logger.info("Timezone validation: fixed %d users with invalid TZ", fixed)
    except Exception as e:
        logger.exception("Timezone validation job failed: %s", e)


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
    sched.add_job(
        run_validate_timezones,
        trigger=CronTrigger(hour=0, minute=15),
        args=(bot,),
        id="validate_timezones",
        replace_existing=True,
    )
    sched.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
