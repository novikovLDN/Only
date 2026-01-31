"""
Unified PaymentService — balance top-up, subscription, idempotency.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import PaymentProvider, PaymentType, UserTier, SUBSCRIPTION_PLANS
from app.integrations.payments.base import CreatePaymentRequest
from app.integrations.payments.providers import get_provider
from app.models.balance import Balance
from app.models.balance_transaction import BalanceTransaction
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.balance_repo import BalanceRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """Unified payment processing."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._payment_repo = PaymentRepository(session)
        self._balance_repo = BalanceRepository(session)
        self._sub_repo = SubscriptionRepository(session)
        self._user_repo = UserRepository(session)

    def _idempotency_key(self) -> str:
        return str(uuid.uuid4())

    async def create_balance_topup(
        self,
        user_id: int,
        amount: Decimal,
        provider: str,
        idempotency_key: str | None = None,
    ) -> tuple[Payment | None, str | None]:
        """
        Create balance top-up. Returns (payment, error).
        Idempotent: same idempotency_key returns existing payment.
        """
        key = idempotency_key or self._idempotency_key()
        existing = await self._payment_repo.get_by_idempotency_key(key)
        if existing:
            logger.info("Idempotent: returning existing payment %s", existing.id)
            return existing, None
        prov = get_provider(provider)
        if not prov:
            return None, f"Provider {provider} not available"
        payment = Payment(
            user_id=user_id,
            provider=provider,
            payment_type=PaymentType.BALANCE_TOPUP,
            amount=amount,
            currency="RUB",
            status="pending",
            idempotency_key=key,
        )
        await self._payment_repo.add(payment)
        await self._session.flush()
        req = CreatePaymentRequest(
            user_id=user_id,
            amount=amount,
            currency="RUB",
            idempotency_key=key,
            description="Пополнение баланса",
            payment_type=PaymentType.BALANCE_TOPUP,
            metadata={"payment_id": payment.id},
        )
        result = await prov.create_payment(req)
        if not result.success:
            payment.status = "failed"
            await self._session.flush()
            return None, result.error or "Unknown error"
        payment.provider_payment_id = result.provider_payment_id
        if result.metadata:
            payment.metadata_json = json.dumps(result.metadata)
        await self._session.flush()
        return payment, None

    async def create_subscription_payment(
        self,
        user_id: int,
        plan_id: str,
        amount: Decimal,
        provider: str,
        idempotency_key: str | None = None,
    ) -> tuple[Payment | None, str | None]:
        """
        Create subscription payment. Returns (payment, error).
        """
        key = idempotency_key or self._idempotency_key()
        existing = await self._payment_repo.get_by_idempotency_key(key)
        if existing:
            return existing, None
        prov = get_provider(provider)
        if not prov:
            return None, f"Provider {provider} not available"
        days = SUBSCRIPTION_PLANS.get(plan_id, 30)
        payment = Payment(
            user_id=user_id,
            provider=provider,
            payment_type=PaymentType.SUBSCRIPTION,
            amount=amount,
            currency="RUB",
            status="pending",
            idempotency_key=key,
            metadata_json=json.dumps({"plan_id": plan_id, "days": days}),
        )
        await self._payment_repo.add(payment)
        await self._session.flush()
        req = CreatePaymentRequest(
            user_id=user_id,
            amount=amount,
            currency="RUB",
            idempotency_key=key,
            description=f"Подписка Premium {plan_id}",
            payment_type=PaymentType.SUBSCRIPTION,
            metadata={"payment_id": payment.id, "plan_id": plan_id},
        )
        result = await prov.create_payment(req)
        if not result.success:
            payment.status = "failed"
            await self._session.flush()
            return None, result.error or "Unknown error"
        payment.provider_payment_id = result.provider_payment_id
        meta = json.loads(payment.metadata_json or "{}")
        if result.metadata:
            meta.update(result.metadata)
        payment.metadata_json = json.dumps(meta)
        await self._session.flush()
        return payment, None

    async def process_webhook(
        self,
        provider: str,
        raw_payload: dict,
        payload_bytes: bytes | None = None,
        signature: str | None = None,
        headers: dict | None = None,
    ) -> tuple[bool, str | None]:
        """
        Process webhook. Idempotent by provider + provider_payment_id.
        Returns (success, error).
        """
        prov = get_provider(provider)
        if not prov:
            return False, f"Unknown provider {provider}"
        payload = await prov.parse_webhook(raw_payload)
        if not payload:
            return True, None  # Ignored event
        if payload.status != "succeeded":
            return True, None
        if payload_bytes and not await prov.verify_webhook(payload_bytes, signature, headers):
            logger.warning("Webhook verification failed: %s", provider)
            # Caller should send admin alert (critical) — see docs/LOAD_AND_CHAOS_TESTING.md
            return False, "Verification failed"
        existing = await self._payment_repo.get_by_provider_id(provider, payload.provider_payment_id)
        if existing:
            if existing.status == "completed":
                logger.info("Idempotent: payment %s already completed", existing.id)
                return True, None
            if existing.status == "pending":
                await self._complete_payment(existing, payload)
                return True, None
            return True, None
        user_id = payload.user_id
        if not user_id:
            logger.warning("Webhook missing user_id: %s", payload.provider_payment_id)
            return False, "Missing user_id"
        payment_type = payload.payment_type or (payload.metadata or {}).get("payment_type", PaymentType.BALANCE_TOPUP)
        payment = Payment(
            user_id=user_id,
            provider=provider,
            provider_payment_id=payload.provider_payment_id,
            payment_type=payment_type,
            amount=payload.amount,
            currency=payload.currency,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            metadata_json=json.dumps(payload.metadata or {}),
        )
        await self._payment_repo.add(payment)
        await self._session.flush()
        await self._complete_payment(payment, payload)
        return True, None

    async def _complete_payment(self, payment: Payment, payload: object = None) -> None:
        """Complete payment — credit balance or activate subscription."""
        from app.integrations.payments.base import WebhookPayload

        p = payload if isinstance(payload, WebhookPayload) else None
        meta = json.loads(payment.metadata_json or "{}") if payment.metadata_json else {}
        if p and p.metadata:
            meta = {**meta, **p.metadata}
        payment.status = "completed"
        payment.completed_at = datetime.now(timezone.utc)
        if payment.payment_type == PaymentType.BALANCE_TOPUP:
            await self._credit_balance(payment.user_id, payment.amount, payment.id)
        elif payment.payment_type == PaymentType.SUBSCRIPTION:
            plan_id = meta.get("plan_id", "monthly")
            days = SUBSCRIPTION_PLANS.get(plan_id, 30)
            await self._activate_subscription(payment.user_id, payment.id, payment.amount, days)
        await self._session.flush()
        logger.info("Payment completed: id=%s type=%s user=%s", payment.id, payment.payment_type, payment.user_id)

    async def _credit_balance(self, user_id: int, amount: Decimal, payment_id: int) -> None:
        """Credit balance and create transaction."""
        balance = await self._balance_repo.get_or_create(user_id)
        balance.amount += amount
        tx = BalanceTransaction(
            user_id=user_id,
            type="credit",
            amount=amount,
            currency="RUB",
            payment_id=payment_id,
        )
        self._session.add(tx)
        await self._session.flush()

    async def _activate_subscription(
        self, user_id: int, payment_id: int, amount: float, days: int
    ) -> None:
        """Create subscription, update user tier, end trial."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=days)
        sub = Subscription(
            user_id=user_id,
            tier=UserTier.PREMIUM,
            started_at=now,
            expires_at=expires,
            is_active=True,
            amount=float(amount),
            payment_id=payment_id,
            auto_renew_from_balance=True,
        )
        self._session.add(sub)
        user = await self._session.get(User, user_id)
        if user:
            user.tier = UserTier.PREMIUM
            user.trial_ends_at = None
        await self._session.flush()
        logger.info("Subscription activated: user=%s expires=%s", user_id, expires)
