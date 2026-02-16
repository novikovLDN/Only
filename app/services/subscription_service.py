"""Subscription / Premium logic."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


TARIFFS = {
    1: 199,
    3: 499,
    6: 799,
    12: 1299,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_users_expiring_soon(
    session: AsyncSession,
    within_hours: float,
) -> list[User]:
    from app.models import User
    threshold = _now() + timedelta(hours=within_hours)
    result = await session.execute(
        select(User).where(
            User.premium_until.isnot(None),
            User.premium_until <= threshold,
            User.premium_until > _now(),
        )
    )
    return list(result.scalars().unique().all())


async def get_expired_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(
            User.premium_until.isnot(None),
            User.premium_until <= _now(),
        )
    )
    return list(result.scalars().unique().all())
