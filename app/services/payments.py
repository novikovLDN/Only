"""Payment service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, User

TARIFF_DAYS = {"1": 30, "3": 90, "12": 365}


async def extend_subscription(session: AsyncSession, user_id: int, days: int) -> None:
    user = await session.get(User, user_id)
    if not user:
        return
    now = datetime.now(timezone.utc)
    pu = user.premium_until
    if pu and (pu.replace(tzinfo=timezone.utc) if pu.tzinfo is None else pu) > now:
        user.premium_until = pu + timedelta(days=days)
    else:
        user.premium_until = now + timedelta(days=days)
    await session.flush()


def get_days_from_payload(payload: str) -> int:
    for k, d in TARIFF_DAYS.items():
        if k in payload:
            return d
    return 30
