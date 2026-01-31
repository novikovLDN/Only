"""
Scheduler initialization — AsyncIOScheduler + SQLAlchemyJobStore (PostgreSQL).

JobStore обеспечивает персистентность jobs между перезапусками.
"""

import logging
from typing import Any

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _get_jobstore_url() -> str:
    """Sync URL для SQLAlchemyJobStore (postgresql://)."""
    return settings.database_url.replace("+asyncpg", "")


def init_scheduler() -> AsyncIOScheduler:
    """
    Create and configure scheduler with PostgreSQL JobStore.
    Does not start — call start() explicitly.
    """
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    jobstores = {
        "default": SQLAlchemyJobStore(url=_get_jobstore_url()),
    }
    _scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        },
    )
    logger.info("Scheduler initialized with SQLAlchemyJobStore")
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
