"""Personal discount service."""

import math
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

DISCOUNT_OPTIONS = [10, 15, 20, 25, 30, 50]
DURATION_OPTIONS_DAYS = [1, 3, 7, 14, 30, 90]


def is_discount_active(user: User | None) -> bool:
    """Check if user has active personal discount."""
    if not user or not user.discount_percent or user.discount_percent <= 0:
        return False
    until = user.discount_until
    if not until:
        return False
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    return until > datetime.now(timezone.utc)


def calculate_price_with_discount(user: User | None, base_price_rub: float) -> tuple[int, int, float]:
    """
    Calculate final price with discount. Returns (final_kopecks, discount_percent, original_rub).
    Uses math.ceil for rounding to whole ruble.
    """
    original = base_price_rub
    discount_pct = 0
    if is_discount_active(user) and user and user.discount_percent:
        discount_pct = min(100, max(0, user.discount_percent))
    if discount_pct <= 0:
        final_rub = original
    else:
        final_rub = math.ceil(original * (100 - discount_pct) / 100)
    final_kopecks = int(final_rub * 100)
    return final_kopecks, discount_pct, original


async def grant_discount(
    session: AsyncSession,
    user_id: int,
    percent: int,
    duration_days: int,
    admin_id: int,
) -> User | None:
    """Grant personal discount to user. Returns user or None."""
    user = await session.get(User, user_id)
    if not user:
        return None
    now = datetime.now(timezone.utc)
    user.discount_percent = min(100, max(1, percent))
    user.discount_until = now + timedelta(days=duration_days)
    user.discount_given_by = admin_id
    user.discount_created_at = now
    await session.flush()
    return user
