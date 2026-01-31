"""
SubscriptionRenewService — автопродление с баланса, retry при неуспехе.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SUBSCRIPTION_PLANS
from app.models.balance_transaction import BalanceTransaction
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.balance_repo import BalanceRepository
from app.repositories.subscription_repo import SubscriptionRepository

logger = logging.getLogger(__name__)

RENEWAL_RETRY_COOLDOWN_HOURS = 72


class SubscriptionRenewService:
    """Autorenew from balance, retry on failure."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sub_repo = SubscriptionRepository(session)
        self._balance_repo = BalanceRepository(session)

    def _renewal_days(self, sub: Subscription) -> int:
        """Infer renewal period from subscription (e.g. monthly=30)."""
        if sub.amount and sub.started_at and sub.expires_at:
            delta = (sub.expires_at - sub.started_at).days
            if delta >= 360:
                return SUBSCRIPTION_PLANS.get("yearly", 365)
            return SUBSCRIPTION_PLANS.get("monthly", 30)
        return SUBSCRIPTION_PLANS.get("monthly", 30)

    def _renewal_amount(self, sub: Subscription) -> Decimal:
        """Amount to charge for renewal."""
        return Decimal(str(sub.amount)) if sub.amount else Decimal("0")

    async def try_renew_from_balance(
        self, sub: Subscription, user: User
    ) -> tuple[bool, str | None]:
        """
        Try to renew subscription by debiting user balance.
        Returns (success, error_message).
        """
        amount = self._renewal_amount(sub)
        if amount <= 0:
            return False, "Invalid renewal amount"
        balance = await self._balance_repo.get_or_create(user.id)
        if balance.amount < amount:
            return False, "Insufficient balance"
        now = datetime.now(timezone.utc)
        days = self._renewal_days(sub)
        new_expires = (sub.expires_at if sub.expires_at > now else now) + timedelta(days=days)
        balance.amount -= amount
        tx = BalanceTransaction(
            user_id=user.id,
            type="subscription",
            amount=amount,
            currency="RUB",
            payment_id=None,
            reference=f"renewal_sub_{sub.id}",
        )
        self._session.add(tx)
        sub.expires_at = new_expires
        sub.last_renewal_attempt_at = now
        await self._session.flush()
        logger.info(
            "Subscription renewed from balance: sub=%s user=%s amount=%s expires=%s",
            sub.id,
            user.id,
            amount,
            new_expires,
        )
        return True, None

    async def mark_renewal_attempted(self, sub: Subscription) -> None:
        """Mark that we attempted renewal (failed)."""
        sub.last_renewal_attempt_at = datetime.now(timezone.utc)
        await self._session.flush()
