"""
Scheduler jobs — habit reminders, trial/subscription notifications.
"""

import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.models.base import get_async_session_maker
from app.scheduler.notifications import (
    run_habit_reminders,
    run_trial_notifications,
    run_subscription_notifications,
)


_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def setup_scheduler(bot) -> None:
    """Configure and start scheduler."""
    sched = get_scheduler()
    # Habit reminders — every 5 minutes check due habits
    sched.add_job(
        run_habit_reminders,
        IntervalTrigger(minutes=5),
        id="habit_reminders",
        args=[bot],
        replace_existing=True,
    )
    # Trial notifications — every hour
    sched.add_job(
        run_trial_notifications,
        IntervalTrigger(hours=1),
        id="trial_notifications",
        args=[bot],
        replace_existing=True,
    )
    # Subscription expiry — every hour
    sched.add_job(
        run_subscription_notifications,
        IntervalTrigger(hours=1),
        id="subscription_notifications",
        args=[bot],
        replace_existing=True,
    )
    sched.start()


def shutdown_scheduler() -> None:
    """Stop scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
