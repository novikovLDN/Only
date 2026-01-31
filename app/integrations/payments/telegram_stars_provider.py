"""
Telegram Stars payment — via native Bot API.
"""

from decimal import Decimal
from typing import Any

from app.integrations.payments.base import BasePaymentProvider, PaymentResult, WebhookPayload


class TelegramStarsProvider(BasePaymentProvider):
    """
    Telegram Stars — uses sendInvoice with currency XTR (Stars).
    Webhook comes as successful_payment in Update.
    """

    async def create_payment(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """
        Telegram Stars: payment is created by sendInvoice in handler.
        This provider just validates — actual creation in handler.
        """
        return PaymentResult(
            success=True,
            payment_id=idempotency_key,
            metadata={"provider": "telegram_stars"},
        )

    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool:
        """Telegram updates are verified by Bot API token."""
        return True

    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse from message.successful_payment."""
        # Called from handler with pre-parsed data
        if "successful_payment" not in payload:
            return None
        sp = payload["successful_payment"]
        return WebhookPayload(
            provider_payment_id=sp.get("telegram_payment_charge_id", ""),
            status="succeeded",
            amount=Decimal(sp.get("total_amount", 0)) / 100,  # Stars in minor units
            currency=sp.get("currency", "XTR"),
            user_id=payload.get("user_id"),
        )
