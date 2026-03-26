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

                # Build reminder text with streak progress
                streak_text = ""
                try:
                    async with sm() as session:
                        streak = await habit_log_service.get_max_streak(session, user.id)
                        if streak > 0:
                            filled = min(10, streak)
                            bar = "🔥" * min(filled, 10) + "⬜" * max(0, 10 - filled)
                            streak_text = f"\n{bar} {streak} days"
                except Exception:
                    pass

                text = t(lang, "notification_format", title=habit.title, time=time_str) + streak_text
                if phrase:
                    text += f"\n\n💬 {phrase}"

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


async def expire_crypto_payments(bot) -> None:
    """Every 5 min: cancel expired crypto payments, notify user, delete invoice messages."""
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.models import Payment, User
    from app.texts import t
    try:
        sm = get_session_maker()
        async with sm() as session:
            now = datetime.now(timezone.utc)
            result = await session.execute(
                select(Payment).where(
                    Payment.provider == "crypto",
                    Payment.status.in_(["check", "pending"]),
                    Payment.expires_at.isnot(None),
                    Payment.expires_at < now,
                )
            )
            payments = result.scalars().all()
            for p in payments:
                p.status = "cancel"
                if bot:
                    try:
                        user = await session.get(User, p.user_id)
                        if user:
                            lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
                            await bot.send_message(chat_id=user.telegram_id, text=t(lang, "crypto_expired"))
                            if p.invoice_message_id:
                                await bot.delete_message(chat_id=user.telegram_id, message_id=p.invoice_message_id)
                    except Exception:
                        pass
            await session.commit()
    except Exception as e:
        logger.exception("Expire crypto payments failed: %s", e)


async def check_premium_expiry(bot) -> None:
    """Daily: notify users whose premium expires in 3 days or 1 day."""
    from datetime import timedelta
    try:
        sm = get_session_maker()
        now = datetime.now(timezone.utc)
        async with sm() as session:
            for days_ahead in (3, 1):
                window_start = now + timedelta(days=days_ahead - 1, hours=23)
                window_end = now + timedelta(days=days_ahead, hours=1)
                result = await session.execute(
                    select(User).where(
                        User.premium_until.isnot(None),
                        User.premium_until > window_start,
                        User.premium_until < window_end,
                    )
                )
                users = result.scalars().all()
                for user in users:
                    try:
                        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
                        text_key = "premium_expiry_3d" if days_ahead == 3 else "premium_expiry_1d"
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=t(lang, text_key),
                        )
                    except Exception as e:
                        logger.warning("Premium expiry notify failed user=%s: %s", user.telegram_id, e)
        logger.info("Premium expiry check completed")
    except Exception as e:
        logger.exception("Premium expiry check failed: %s", e)


async def send_weekly_report(bot) -> None:
    """Weekly (Monday 09:00 UTC): send habit completion report to all users."""
    from datetime import timedelta
    from sqlalchemy import func
    from app.models import HabitLog
    try:
        sm = get_session_maker()
        now = datetime.now(timezone.utc)
        week_start = (now - timedelta(days=7)).date()

        async with sm() as session:
            users_result = await session.execute(select(User))
            users = users_result.scalars().all()

            for user in users:
                try:
                    # Count done and skipped for the week
                    done_count = await session.scalar(
                        select(func.count()).select_from(HabitLog).where(
                            HabitLog.user_id == user.id,
                            HabitLog.status == "done",
                            HabitLog.log_date >= week_start,
                        )
                    ) or 0
                    skip_count = await session.scalar(
                        select(func.count()).select_from(HabitLog).where(
                            HabitLog.user_id == user.id,
                            HabitLog.status == "skip",
                            HabitLog.log_date >= week_start,
                        )
                    ) or 0

                    total = done_count + skip_count
                    if total == 0:
                        continue  # Skip inactive users

                    pct = int((done_count / total) * 100) if total > 0 else 0
                    filled = min(10, pct // 10)
                    bar = "🟩" * filled + "⬜" * (10 - filled)

                    lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
                    text = t(lang, "weekly_report",
                             done=done_count, skip=skip_count,
                             pct=pct, bar=bar)

                    await bot.send_message(chat_id=user.telegram_id, text=text)
                except Exception as e:
                    logger.warning("Weekly report failed user=%s: %s", user.telegram_id, e)

        logger.info("Weekly reports sent")
    except Exception as e:
        logger.exception("Weekly report job failed: %s", e)


def setup_scheduler(bot) -> None:
    sched = get_scheduler()
    sched.add_job(
        expire_crypto_payments,
        trigger="interval",
        minutes=5,
        args=(bot,),
        id="expire_crypto_payments",
        replace_existing=True,
    )
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
        check_premium_expiry,
        trigger=CronTrigger(hour=10, minute=0),
        args=(bot,),
        id="premium_expiry_check",
        replace_existing=True,
    )
    sched.add_job(
        send_weekly_report,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        args=(bot,),
        id="weekly_report",
        replace_existing=True,
    )
    sched.start()
    logger.info("Scheduler started with %d jobs", len(sched.get_jobs()))


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
