"""
YooKassa payment provider.
"""

import json
from decimal import Decimal
from typing import Any

from app.config import settings
from app.config.constants import PaymentProvider
from app.integrations.payments.base import BasePaymentProvider, PaymentResult, WebhookPayload


class YooKassaProvider(BasePaymentProvider):
    """YooKassa integration."""

    async def create_payment(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Create YooKassa payment."""
        if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
            return PaymentResult(success=False, error="YooKassa not configured")
        try:
            from yookassa import Payment, Configuration

            Configuration.configure(settings.yookassa_shop_id, settings.yookassa_secret_key)
            payment = Payment.create(
                {
                    "amount": {"value": str(amount), "currency": currency},
                    "confirmation": {"type": "redirect", "return_url": "https://t.me/your_bot"},
                    "capture": True,
                    "description": description,
                    "metadata": {"user_id": user_id, **(metadata or {})},
                },
                idempotency_key,
            )
            return PaymentResult(
                success=True,
                payment_id=payment.id,
                payment_url=payment.confirmation.redirect_url if payment.confirmation else None,
            )
        except Exception as e:
            return PaymentResult(success=False, error=str(e))

    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool:
        """YooKassa uses IP whitelist; optional body verification."""
        # In production: verify notification secret
        return True

    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse YooKassa notification."""
        if payload.get("event") != "payment.succeeded":
            return None
        obj = payload.get("object", {})
        if obj.get("status") != "succeeded":
            return None
        metadata = obj.get("metadata", {})
        return WebhookPayload(
            provider_payment_id=obj.get("id", ""),
            status="succeeded",
            amount=Decimal(str(obj.get("amount", {}).get("value", 0))),
            currency=obj.get("amount", {}).get("currency", "RUB"),
            user_id=metadata.get("user_id"),
        )
