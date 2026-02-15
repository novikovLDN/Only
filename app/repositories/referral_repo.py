"""Referral repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, inviter_id: int, invited_id: int) -> Referral:
        ref = Referral(inviter_id=inviter_id, invited_id=invited_id)
        self.session.add(ref)
        await self.session.flush()
        return ref

    async def exists(self, inviter_id: int, invited_id: int) -> bool:
        result = await self.session.execute(
            select(Referral).where(
                Referral.inviter_id == inviter_id,
                Referral.invited_id == invited_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_by_inviter(self, inviter_id: int) -> int:
        result = await self.session.execute(select(Referral).where(Referral.inviter_id == inviter_id))
        return len(result.scalars().all())
