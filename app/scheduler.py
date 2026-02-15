"""APScheduler — habit reminders, motivation phrases, ReplyKeyboard."""

import logging
from datetime import date, datetime
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
    """Send habit reminders — timezone-aware, motivation phrase, confirm/decline keyboard."""
    from app.core.database import get_session_maker
    from app.repositories.habit_repo import HabitRepository
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.repositories.motivation_repo import MotivationRepository
    from app.services.motivation_service import MotivationService
    from app.utils.i18n import t
    from app.keyboards.inline import habit_confirm_decline

    try:
        sm = get_session_maker()
        async with sm() as session:
            habit_repo = HabitRepository(session)
            habit_log_repo = HabitLogRepository(session)
            motivation_repo = MotivationRepository(session)
            motivation_svc = MotivationService(motivation_repo)
            items = await habit_repo.get_all_for_reminders()
            for habit, user, days, times in items:
                tz_name = getattr(user, "timezone", None) or "UTC"
                tz = ZoneInfo(tz_name)
                now_dt = datetime.now(tz)
                today_weekday = now_dt.weekday()
                today = now_dt.date()
                now_hour, now_min = now_dt.hour, now_dt.minute
                if today_weekday not in days:
                    continue
                for tt in times:
                    if tt.hour == now_hour and tt.minute == now_min:
                        try:
                            if await habit_log_repo.exists_for_user_habit_date(user.id, habit.id, today):
                                continue
                            lang = getattr(user, "language", None)
                            if lang not in ("ru", "en"):
                                lang = "ru"
                            phrase = await motivation_svc.get_random_phrase(lang)
                            log = await habit_log_repo.create_pending(user.id, habit.id, today)
                            await session.commit()
                            _t = lambda k, **kw: t(lang, k, **kw)
                            msg = f"📌 {habit.title}\n\n{phrase}"
                            await bot.send_message(
                                chat_id=user.telegram_id,
                                text=msg,
                                reply_markup=habit_confirm_decline(_t, log.id),
                            )
                        except Exception as e:
                            logger.warning("Reminder failed: %s", e)
                            await session.rollback()
    except Exception as e:
        logger.exception("Reminders job error: %s", e)


async def run_mark_missed_and_recalc(bot) -> None:
    """Mark pending as missed after 24h, recalc daily_progress. Run hourly."""
    from app.core.database import get_session_maker
    from app.services.progress_service import ProgressService
    from sqlalchemy import select
    from app.core.models import HabitLog, User

    try:
        sm = get_session_maker()
        async with sm() as session:
            result = await session.execute(select(HabitLog).where(HabitLog.status == "pending"))
            pendings = list(result.scalars().unique().all())
            user_dates_to_recalc = set()
            for log in pendings:
                user = await session.get(User, log.user_id)
                if not user:
                    continue
                tz = ZoneInfo(getattr(user, "timezone", None) or "UTC")
                now_local = datetime.now(tz).date()
                if (now_local - log.date).days >= 1:
                    log.status = "missed"
                    user_dates_to_recalc.add((log.user_id, log.date))
            await session.flush()
            progress_svc = ProgressService(session)
            for uid, d in user_dates_to_recalc:
                await progress_svc.recalc_daily_for_user(uid, d)
            await session.commit()
    except Exception as e:
        logger.exception("Mark missed job error: %s", e)


def setup_scheduler(bot) -> None:
    sched = get_scheduler()
    sched.add_job(run_reminders, IntervalTrigger(minutes=1), args=(bot,), id="habit_reminders")
    sched.add_job(run_mark_missed_and_recalc, IntervalTrigger(hours=1), args=(bot,), id="mark_missed_recalc")
    sched.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
