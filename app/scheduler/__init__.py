"""
Scheduler — APScheduler с PostgreSQL JobStore.

Jobs: habit reminders, trial/subscription notifications, health checks.
"""

from app.scheduler.init import get_scheduler, init_scheduler, shutdown_scheduler
from app.scheduler.registry import add_job, remove_job, update_job

__all__ = [
    "get_scheduler",
    "init_scheduler",
    "shutdown_scheduler",
    "add_job",
    "remove_job",
    "update_job",
]
