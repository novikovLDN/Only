"""Referral service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Referral, User


async def create_referral(
    session: AsyncSession,
    referrer_id: int,
    referral_user_id: int,
) -> Referral | None:
    if referrer_id == referral_user_id:
        return None
    existing = await session.execute(
        select(Referral).where(
            Referral.referrer_id == referrer_id,
            Referral.referral_user_id == referral_user_id,
        )
    )
    if existing.scalar_one_or_none():
        return None
    ref = Referral(referrer_id=referrer_id, referral_user_id=referral_user_id)
    session.add(ref)
    await session.flush()
    await session.refresh(ref)
    return ref


async def get_referral(
    session: AsyncSession,
    referrer_id: int,
    referral_user_id: int,
) -> Referral | None:
    result = await session.execute(
        select(Referral).where(
            Referral.referrer_id == referrer_id,
            Referral.referral_user_id == referral_user_id,
        )
    )
    return result.scalar_one_or_none()


async def count_referrals(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func
    result = await session.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == user_id)
    )
    return result.scalar() or 0


async def give_reward_if_pending(
    session: AsyncSession,
    referral: Referral,
) -> bool:
    if referral.reward_given:
        return False
    referral.reward_given = True
    referrer = await session.get(User, referral.referrer_id)
    if referrer:
        from app.services.user_service import add_reward_days
        await add_reward_days(session, referrer, 7)
    await session.flush()
    return True
