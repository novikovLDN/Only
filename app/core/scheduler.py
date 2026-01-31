"""
APScheduler setup.

Регистрация jobs (habit reminders, trial/subscription notifications).
"""

# Re-export from scheduler
from app.scheduler.init import get_scheduler, shutdown_scheduler
from app.scheduler.jobs import setup_scheduler
