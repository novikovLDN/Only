"""
Subscription repository.
"""

from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Subscription data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Subscription)

    async def get_active_subscription(self, user_id: int) -> Subscription | None:
        """Get active subscription for user."""
        now = datetime.utcnow()
        result = await self._session.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.is_active == True,
                    Subscription.expires_at > now,
                )
            )
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_expiring_soon(
        self, hours_ahead: int
    ) -> list[Subscription]:
        """Get subscriptions expiring within hours."""
        from datetime import timedelta

        now = datetime.utcnow()
        deadline = now + timedelta(hours=hours_ahead)
        result = await self._session.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.is_active == True,
                    Subscription.expires_at > now,
                    Subscription.expires_at <= deadline,
                )
            )
        )
        return list(result.scalars().all())
