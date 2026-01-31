"""
Referral service with anti-fraud.
"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import Referral
from app.models.user import User
from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository
from app.services.anti_fraud_service import AntiFraudService


class ReferralService:
    """Referral logic with anti self-referral and multi-account checks."""

    REFERRAL_REWARD = Decimal("50.00")

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ref_repo = ReferralRepository(session)
        self._user_repo = UserRepository(session)
        self._antifraud = AntiFraudService(session)

    async def apply_referral(
        self, referred_user_id: int, referral_code: str
    ) -> tuple[bool, str]:
        """
        Apply referral when new user signs up with code.
        Returns (success, message).
        """
        referrer = await self._user_repo.get_by_referral_code(referral_code)
        if not referrer:
            return False, "Неверный реферальный код."
        if referrer.id == referred_user_id:
            return False, "Нельзя использовать свой код."
        existing = await self._ref_repo.get_referral(referrer.id, referred_user_id)
        if existing:
            return False, "Реферал уже учтён."
        is_suspicious = await self._antifraud.check_referral_suspicious(referrer.id, referred_user_id)
        ref = Referral(
            referrer_id=referrer.id,
            referred_id=referred_user_id,
            referral_code=referral_code,
            is_suspicious=is_suspicious,
        )
        await self._ref_repo.add(ref)
        referred = await self._user_repo.get_by_telegram_id(referred_user_id)
        if referred:
            referred.referred_by_id = referrer.id
            await self._session.flush()
        return True, "Реферал применён."
