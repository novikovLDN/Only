"""
Scheduler jobs — habit reminders, trial, subscription, health check.

Каждый job idempotent: можно безопасно перезапустить.
Перед отправкой — проверка актуального статуса пользователя.
"""

import logging

from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler.init import get_scheduler, init_scheduler, shutdown_scheduler
from app.scheduler.job_runner import (
    run_analytics_refresh_job,
    run_habit_reminders_job,
    run_health_check_job,
    run_retention_job,
    run_subscription_notifications_job,
    run_subscription_renew_job,
    run_trial_notifications_job,
)
from app.scheduler.registry import (
    JOB_ANALYTICS_REFRESH,
    JOB_HABIT_REMINDERS,
    JOB_HEALTH_CHECK,
    JOB_RETENTION,
    JOB_SUBSCRIPTION_NOTIFICATIONS,
    JOB_SUBSCRIPTION_RENEW,
    JOB_TRIAL_NOTIFICATIONS,
    add_job,
)

logger = logging.getLogger(__name__)


def setup_scheduler(bot) -> None:
    """Initialize scheduler, register jobs, start."""
    init_scheduler()
    add_job(
        run_habit_reminders_job,
        IntervalTrigger(minutes=5),
        JOB_HABIT_REMINDERS,
        args=(bot,),
    )
    add_job(
        run_trial_notifications_job,
        IntervalTrigger(hours=1),
        JOB_TRIAL_NOTIFICATIONS,
        args=(bot,),
    )
    add_job(
        run_subscription_notifications_job,
        IntervalTrigger(hours=1),
        JOB_SUBSCRIPTION_NOTIFICATIONS,
        args=(bot,),
    )
    add_job(
        run_subscription_renew_job,
        IntervalTrigger(hours=6),
        JOB_SUBSCRIPTION_RENEW,
        args=(bot,),
    )
    add_job(
        run_retention_job,
        IntervalTrigger(hours=12),
        JOB_RETENTION,
        args=(bot,),
    )
    add_job(
        run_health_check_job,
        IntervalTrigger(minutes=5),
        JOB_HEALTH_CHECK,
        args=(bot,),
    )
    add_job(
        run_analytics_refresh_job,
        IntervalTrigger(hours=1),
        JOB_ANALYTICS_REFRESH,
    )
    sched = get_scheduler()
    sched.start()
    logger.info("Scheduler started with %d jobs", len(sched.get_jobs()))
