"""
YooKassa payment provider.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Any

from app.config import settings
from app.integrations.payments.base import (
    BasePaymentProvider,
    CreatePaymentRequest,
    PaymentResult,
    WebhookPayload,
)

logger = logging.getLogger(__name__)


class YooKassaProvider(BasePaymentProvider):
    """YooKassa integration."""

    @property
    def name(self) -> str:
        return "yookassa"

    async def create_payment(self, request: CreatePaymentRequest) -> PaymentResult:
        """Create YooKassa payment. Retry 3x on transient failures (timeout, 5xx)."""
        if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
            logger.warning("YooKassa not configured")
            return PaymentResult(success=False, error="YooKassa not configured")

        def _create() -> Any:
            from yookassa import Configuration, Payment

            Configuration.configure(settings.yookassa_shop_id, settings.yookassa_secret_key)
            metadata = {"user_id": request.user_id, "payment_type": request.payment_type}
            if request.metadata:
                metadata.update(request.metadata)
            return Payment.create(
                {
                    "amount": {"value": str(request.amount), "currency": request.currency},
                    "confirmation": {"type": "redirect", "return_url": "https://t.me/"},
                    "capture": True,
                    "description": request.description,
                    "metadata": metadata,
                },
                request.idempotency_key,
            )

        last_err: str | None = None
        for attempt in range(3):
            try:
                payment = await asyncio.to_thread(_create)
                url = payment.confirmation.redirect_url if payment.confirmation else None
                return PaymentResult(
                    success=True,
                    provider_payment_id=payment.id,
                    payment_url=url,
                )
            except Exception as e:
                last_err = str(e)
                if attempt < 2:
                    delay = 1.0 * (2**attempt)
                    logger.warning("YooKassa retry %d/3 in %.0fs: %s", attempt + 1, delay, e)
                    await asyncio.sleep(delay)
                else:
                    logger.exception("YooKassa create_payment failed after 3 attempts: %s", e)
        return PaymentResult(success=False, error=last_err or "Unknown error")

    async def verify_webhook(
        self, payload: bytes, signature: str | None, headers: dict | None
    ) -> bool:
        """YooKassa: IP whitelist. Optional: verify object_id in payload."""
        return True

    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse YooKassa notification."""
        if payload.get("event") != "payment.succeeded":
            return None
        obj = payload.get("object", {})
        if obj.get("status") != "succeeded":
            return None
        meta = obj.get("metadata", {})
        return WebhookPayload(
            provider_payment_id=obj.get("id", ""),
            status="succeeded",
            amount=Decimal(str(obj.get("amount", {}).get("value", 0))),
            currency=obj.get("amount", {}).get("currency", "RUB"),
            user_id=meta.get("user_id"),
            payment_type=meta.get("payment_type"),
            metadata=meta,
        )
