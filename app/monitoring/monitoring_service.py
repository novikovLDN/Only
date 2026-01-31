"""
MonitoringService — health aggregation, DB logging.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.config.constants import AlertSeverity
from app.models.base import get_async_session_maker
from app.models.system_log import SystemLog

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


@dataclass
class ComponentStatus:
    """Single component health."""

    name: str
    ok: bool
    message: str = ""


@dataclass
class AggregatedHealth:
    """Aggregated health status."""

    ok: bool
    components: dict[str, ComponentStatus] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringService:
    """Health checks + DB logging."""

    def __init__(self, bot: "Bot | None" = None) -> None:
        self._bot = bot

    async def check_database(self) -> ComponentStatus:
        """Check DB connection."""
        try:
            session_factory = get_async_session_maker()
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            return ComponentStatus("database", True)
        except Exception as e:
            logger.warning("Health check database failed: %s", e)
            return ComponentStatus("database", False, str(e))

    async def check_scheduler(self) -> ComponentStatus:
        """Check scheduler running."""
        try:
            from app.scheduler.init import get_scheduler

            sched = get_scheduler()
            return ComponentStatus("scheduler", sched.running or False)
        except Exception as e:
            logger.warning("Health check scheduler failed: %s", e)
            return ComponentStatus("scheduler", False, str(e))

    async def check_bot(self) -> ComponentStatus:
        """Check bot alive (getMe)."""
        if not self._bot:
            return ComponentStatus("bot", True, "skipped")
        try:
            me = await self._bot.get_me()
            return ComponentStatus("bot", me is not None)
        except Exception as e:
            logger.warning("Health check bot failed: %s", e)
            return ComponentStatus("bot", False, str(e))

    async def run_health_checks(self) -> AggregatedHealth:
        """Run all checks, return aggregated status."""
        db = await self.check_database()
        sched = await self.check_scheduler()
        bot = await self.check_bot()
        components = {db.name: db, sched.name: sched, bot.name: bot}
        ok = all(c.ok for c in components.values())
        return AggregatedHealth(ok=ok, components=components)

    async def log_to_db(
        self,
        severity: str,
        source: str,
        message: str,
        details: dict | None = None,
        fingerprint: str | None = None,
    ) -> None:
        """Persist log to system_logs."""
        try:
            session_factory = get_async_session_maker()
            async with session_factory() as session:
                log = SystemLog(
                    severity=severity,
                    source=source,
                    message=message[:500],
                    details=json.dumps(details) if details else None,
                    fingerprint=fingerprint,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            logger.exception("Failed to log to DB: %s", e)
