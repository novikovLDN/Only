"""
Scheduler initialization — AsyncIOScheduler with in-memory JobStore.

Jobs восстанавливаются при startup через setup_scheduler() из jobs.py.
Без psycopg2 — полностью async архитектура.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def init_scheduler() -> AsyncIOScheduler:
    """
    Create scheduler (in-memory, no JobStore).
    Does not start — call start() explicitly.
    """
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        },
    )
    logger.info("Scheduler initialized (in-memory)")
    return _scheduler


def get_scheduler() -> AsyncIOScheduler:
    """Get scheduler instance. Raises if not initialized."""
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    return _scheduler


async def shutdown_scheduler() -> None:
    """Graceful shutdown — wait for running jobs."""
    global _scheduler
    if _scheduler is None:
        return
    logger.info("Shutting down scheduler...")
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")
