"""
Unified payment service — balance top-up, subscription, idempotency.
"""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import PaymentProvider, PaymentType
from app.integrations.payments.yookassa_provider import YooKassaProvider
from app.models.payment import Payment
from app.models.balance import Balance
from app.repositories.payment_repo import PaymentRepository
from app.repositories.balance_repo import BalanceRepository


class PaymentService:
    """Unified payment processing with idempotency."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._payment_repo = PaymentRepository(session)
        self._balance_repo = BalanceRepository(session)
        self._yookassa = YooKassaProvider()

    def _idempotency_key(self) -> str:
        return str(uuid.uuid4())

    async def create_balance_topup(
        self,
        user_id: int,
        amount: Decimal,
        provider: str,
    ) -> tuple[Payment | None, str | None]:
        """
        Create balance top-up payment. Returns (payment, error).
        """
        idem_key = self._idempotency_key()
        existing = await self._payment_repo.get_by_idempotency_key(idem_key)
        if existing:
            return existing, None
        payment = Payment(
            user_id=user_id,
            provider=provider,
            payment_type=PaymentType.BALANCE_TOPUP,
            amount=amount,
            currency="RUB",
            status="pending",
            idempotency_key=idem_key,
        )
        await self._payment_repo.add(payment)
        if provider == PaymentProvider.YOOKASSA:
            result = await self._yookassa.create_payment(
                user_id=user_id,
                amount=amount,
                currency="RUB",
                idempotency_key=idem_key,
                description="Пополнение баланса",
                metadata={"payment_id": payment.id},
            )
            if result.success and result.payment_id:
                payment.provider_payment_id = result.payment_id
                await self._session.flush()
                return payment, None
            return None, result.error or "Unknown error"
        return payment, None

    async def process_webhook(
        self,
        provider: str,
        provider_payment_id: str,
        status: str,
        amount: Decimal,
        user_id: int | None,
    ) -> bool:
        """
        Process webhook — idempotent. Returns True if processed.
        """
        existing = await self._payment_repo.get_by_provider_id(provider, provider_payment_id)
        if existing:
            if existing.status == "completed":
                return True  # Already processed
            if status == "succeeded":
                await self._complete_payment(existing, user_id)
            return True
        if status == "succeeded" and user_id:
            payment = Payment(
                user_id=user_id,
                provider=provider,
                provider_payment_id=provider_payment_id,
                payment_type=PaymentType.BALANCE_TOPUP,
                amount=amount,
                currency="RUB",
                status="completed",
            )
            await self._payment_repo.add(payment)
            await self._credit_balance(user_id, amount)
            payment.completed_at = datetime.utcnow()
            await self._session.flush()
        return True

    async def _complete_payment(self, payment: Payment, user_id: int | None) -> None:
        """Mark payment complete and credit balance."""
        uid = user_id or payment.user_id
        payment.status = "completed"
        payment.completed_at = datetime.utcnow()
        await self._credit_balance(uid, payment.amount)
        await self._session.flush()

    async def _credit_balance(self, user_id: int, amount: Decimal) -> None:
        """Add amount to user balance."""
        balance = await self._balance_repo.get_or_create(user_id)
        balance.amount += amount
        await self._session.flush()
