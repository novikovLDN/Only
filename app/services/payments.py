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
    base = user.subscription_until if user.subscription_until and user.subscription_until > now else now
    user.subscription_until = base + timedelta(days=days)
    await session.flush()


def get_days_from_payload(payload: str) -> int:
    for k, d in TARIFF_DAYS.items():
        if k in payload:
            return d
    return 30
