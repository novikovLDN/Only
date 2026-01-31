"""
System log repository.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_log import SystemLog
from app.repositories.base import BaseRepository


class SystemLogRepository(BaseRepository[SystemLog]):
    """System log data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SystemLog)

    async def get_recent_by_fingerprint(
        self, fingerprint: str, since_minutes: int = 5
    ) -> SystemLog | None:
        """Check if similar alert was sent recently (deduplication)."""
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        result = await self._session.execute(
            select(SystemLog)
            .where(
                and_(
                    SystemLog.fingerprint == fingerprint,
                    SystemLog.created_at > since,
                    SystemLog.alerted_at.isnot(None),
                )
            )
            .order_by(SystemLog.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
