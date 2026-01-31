"""
Referral repository.
"""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import Referral
from app.repositories.base import BaseRepository


class ReferralRepository(BaseRepository[Referral]):
    """Referral data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Referral)

    async def get_referral(self, referrer_id: int, referred_id: int) -> Referral | None:
        """Get referral record between two users."""
        result = await self._session.execute(
            select(Referral).where(
                and_(
                    Referral.referrer_id == referrer_id,
                    Referral.referred_id == referred_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def count_referrals(self, referrer_id: int) -> int:
        """Count referrals by user."""
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == referrer_id)
        )
        return result.scalar() or 0
