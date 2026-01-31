"""
Health check endpoints for Railway/deployment.

Each check returns bool. All must pass for 200 OK.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.models.base import get_async_session_maker

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


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
    except Exception as e:
        logger.warning("Health check DB failed: %s", e)
        return False


async def check_scheduler() -> bool:
    """Verify scheduler is running."""
    try:
        from app.scheduler.init import get_scheduler

        sched = get_scheduler()
        return sched.running
    except Exception as e:
        logger.warning("Health check scheduler failed: %s", e)
        return False


async def check_bot(bot: "Bot") -> bool:
    """Verify Telegram bot is reachable (getMe)."""
    try:
        me = await bot.get_me()
        return me is not None
    except Exception as e:
        logger.warning("Health check bot failed: %s", e)
        return False


async def full_health_check(bot: "Bot | None" = None) -> HealthStatus:
    """
    Run all health checks.

    Args:
        bot: Optional. If provided, verifies bot connectivity via get_me().
    """
    db_ok = await check_db()
    sched_ok = await check_scheduler()
    bot_ok = await check_bot(bot) if bot else True  # Skip if no bot yet

    ok = db_ok and sched_ok and bot_ok
    return HealthStatus(
        ok=ok,
        details={
            "database": db_ok,
            "scheduler": sched_ok,
            "bot": bot_ok,
        },
    )
