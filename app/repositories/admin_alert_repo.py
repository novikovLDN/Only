"""Admin alert repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_alert import AdminAlert
from app.repositories.base import BaseRepository


class AdminAlertRepository(BaseRepository[AdminAlert]):
    """Admin alert data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdminAlert)

    async def was_alerted_recently(
        self, fingerprint: str, within_minutes: int
    ) -> bool:
        """Check if we sent alert with this fingerprint within cooldown."""
        since = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
        result = await self._session.execute(
            select(AdminAlert)
            .where(
                and_(
                    AdminAlert.fingerprint == fingerprint,
                    AdminAlert.created_at > since,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_recent(self, limit: int = 10) -> list:
        """Get recent alerts."""
        result = await self._session.execute(
            select(AdminAlert).order_by(desc(AdminAlert.created_at)).limit(limit)
        )
        return list(result.scalars().all())
