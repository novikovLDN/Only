"""
Health check endpoints for Railway/deployment.
"""

from dataclasses import dataclass

from sqlalchemy import text

from app.models.base import get_async_session_maker


@dataclass
class HealthStatus:
    """Health check result."""

    ok: bool
    details: dict[str, bool | str]


async def check_db() -> bool:
    """Verify database connection."""
    try:
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_scheduler() -> bool:
    """Verify scheduler is running."""
    try:
        from app.scheduler.jobs import get_scheduler

        sched = get_scheduler()
        return sched.running
    except Exception:
        return False


async def full_health_check() -> HealthStatus:
    """Run all health checks."""
    db_ok = await check_db()
    sched_ok = await check_scheduler()
    ok = db_ok and sched_ok
    return HealthStatus(
        ok=ok,
        details={
            "database": db_ok,
            "scheduler": sched_ok,
        },
    )
