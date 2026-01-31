"""
Subscription repository.
"""

from datetime import datetime, timezone

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Subscription data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Subscription)

    async def get_active_subscription(self, user_id: int) -> Subscription | None:
        """Get active subscription for user."""
        now = datetime.now(timezone.utc)
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

    async def count_active(self) -> int:
        """Count active subscriptions."""
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.is_active == True,
                    Subscription.expires_at > now,
                )
            )
        )
        return result.scalar() or 0

    async def sum_revenue(self) -> float:
        """Sum of subscription amounts (paid)."""
        result = await self._session.execute(
            select(func.coalesce(func.sum(Subscription.amount), 0)).where(
                Subscription.amount.isnot(None)
            )
        )
        val = result.scalar()
        return float(val) if val is not None else 0.0

    async def get_expiring_for_renewal(
        self, within_hours: int = 24
    ) -> list[tuple[Subscription, object]]:
        """Subscriptions expiring soon with auto_renew enabled. Returns (sub, user) via join."""
        from datetime import timedelta

        from app.models.user import User

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=within_hours)
        result = await self._session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                and_(
                    Subscription.is_active == True,
                    Subscription.auto_renew_from_balance == True,
                    Subscription.expires_at > now,
                    Subscription.expires_at <= deadline,
                )
            )
        )
        return list(result.all())

    async def get_expired_for_retry(
        self, retry_cooldown_hours: int = 72
    ) -> list[tuple[Subscription, object]]:
        """Expired subscriptions with auto_renew, ready for retry (cooldown passed)."""
        from datetime import timedelta

        from app.models.user import User

        now = datetime.now(timezone.utc)
        cooldown = now - timedelta(hours=retry_cooldown_hours)
        result = await self._session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                and_(
                    Subscription.is_active == True,
                    Subscription.auto_renew_from_balance == True,
                    Subscription.expires_at < now,
                    (Subscription.last_renewal_attempt_at.is_(None))
                    | (Subscription.last_renewal_attempt_at < cooldown),
                )
            )
        )
        return list(result.all())

    async def get_expiring_soon(
        self, hours_ahead: int
    ) -> list[Subscription]:
        """Get subscriptions expiring within hours."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
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
