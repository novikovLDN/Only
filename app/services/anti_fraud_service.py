"""
Anti-fraud: self-referral, multi-account detection.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.referral import Referral


class AntiFraudService:
    """Anti-fraud checks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_referral_suspicious(self, referrer_id: int, referred_id: int) -> bool:
        """
        Check if referral might be fraudulent (same device, IP pattern, etc.).
        Returns True if suspicious.
        """
        referrer = await self._session.get(User, referrer_id)
        referred = await self._session.get(User, referred_id)
        if not referrer or not referred:
            return True
        if referrer.device_fingerprint and referred.device_fingerprint:
            if referrer.device_fingerprint == referred.device_fingerprint:
                return True
        return False

    async def count_accounts_by_fingerprint(self, fingerprint: str) -> int:
        """Count users with same device fingerprint."""
        result = await self._session.execute(
            select(func.count(User.id)).where(User.device_fingerprint == fingerprint)
        )
        return result.scalar() or 0
