"""Trial premium service — 3-day free trial for new users."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)


async def grant_trial_if_eligible(session: AsyncSession, user: User) -> bool:
    """Grant trial premium to a new user if they haven't used it before.

    Returns True if trial was granted.
    """
    if user.trial_used:
        return False

    if user.premium_until and user.premium_until > datetime.now(timezone.utc):
        return False

    trial_days = settings.trial_days
    if trial_days <= 0:
        return False

    user.trial_used = True
    user.premium_until = datetime.now(timezone.utc) + timedelta(days=trial_days)
    await session.flush()
    logger.info("Trial premium granted to user_id=%s for %d days", user.id, trial_days)
    return True
