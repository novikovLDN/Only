"""
Job registration API — add, remove, update.

Job IDs детерминированные для предсказуемости и idempotent updates.
"""

import logging
from typing import Any, Callable

from apscheduler.triggers.base import BaseTrigger

from app.scheduler.init import get_scheduler

logger = logging.getLogger(__name__)

# Детерминированные ID jobs
JOB_HABIT_REMINDERS = "habit_reminders"
JOB_TRIAL_NOTIFICATIONS = "trial_notifications"
JOB_SUBSCRIPTION_NOTIFICATIONS = "subscription_notifications"
JOB_HEALTH_CHECK = "health_check"
JOB_ANALYTICS_REFRESH = "analytics_refresh"
JOB_SUBSCRIPTION_RENEW = "subscription_renew"
JOB_RETENTION = "retention"


def add_job(
    func: Callable,
    trigger: BaseTrigger,
    job_id: str,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    replace_existing: bool = True,
) -> Any:
    """
    Add or replace job.
    Idempotent: replace_existing=True обновляет существующий job.
    """
    sched = get_scheduler()
    job = sched.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args or (),
        kwargs=kwargs or {},
        replace_existing=replace_existing,
    )
    logger.info("Job added: %s", job_id)
    return job


def remove_job(job_id: str) -> bool:
    """Remove job by ID. Returns True if removed."""
    sched = get_scheduler()
    try:
        sched.remove_job(job_id)
        logger.info("Job removed: %s", job_id)
        return True
    except Exception as e:
        logger.warning("Failed to remove job %s: %s", job_id, e)
        return False


def update_job(
    job_id: str,
    trigger: BaseTrigger | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
) -> bool:
    """Update job. Returns True if updated."""
    sched = get_scheduler()
    try:
        job = sched.get_job(job_id)
        if job is None:
            return False
        updates: dict[str, Any] = {}
        if trigger is not None:
            updates["trigger"] = trigger
        if args is not None:
            updates["args"] = args
        if kwargs is not None:
            updates["kwargs"] = kwargs
        job.modify(**updates)
        logger.info("Job updated: %s", job_id)
        return True
    except Exception as e:
        logger.warning("Failed to update job %s: %s", job_id, e)
        return False
