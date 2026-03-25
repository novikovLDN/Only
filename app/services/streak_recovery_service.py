"""Streak recovery service — allow users to recover a broken streak."""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.user_service import is_premium

logger = logging.getLogger(__name__)

# Free users get 1 recovery per 30 days, premium users get 3
FREE_RECOVERIES_PER_MONTH = 1
PREMIUM_RECOVERIES_PER_MONTH = 3


def get_max_recoveries(user: User) -> int:
    """Get max recoveries allowed per month based on premium status."""
    return PREMIUM_RECOVERIES_PER_MONTH if is_premium(user) else FREE_RECOVERIES_PER_MONTH


def can_recover_streak(user: User) -> bool:
    """Check if user can use streak recovery."""
    max_recoveries = get_max_recoveries(user)
    used = user.streak_recoveries_used or 0

    # Reset counter if last recovery was more than 30 days ago
    if user.last_streak_recovery_at:
        days_since = (datetime.now(timezone.utc) - user.last_streak_recovery_at).days
        if days_since >= 30:
            return True  # Counter will be reset on use

    return used < max_recoveries


async def use_streak_recovery(session: AsyncSession, user: User) -> bool:
    """Use one streak recovery. Returns True if successful."""
    if not can_recover_streak(user):
        return False

    now = datetime.now(timezone.utc)

    # Reset counter if 30+ days since last recovery
    if user.last_streak_recovery_at:
        days_since = (now - user.last_streak_recovery_at).days
        if days_since >= 30:
            user.streak_recoveries_used = 0

    user.streak_recoveries_used = (user.streak_recoveries_used or 0) + 1
    user.last_streak_recovery_at = now
    await session.flush()
    logger.info("Streak recovery used by user_id=%s (used=%d)", user.id, user.streak_recoveries_used)
    return True
