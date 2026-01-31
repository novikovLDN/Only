"""
Telegram Stars payment — native Bot API sendInvoice.
"""

from decimal import Decimal
import logging
from typing import Any

from app.integrations.payments.base import (
    BasePaymentProvider,
    CreatePaymentRequest,
    PaymentResult,
    WebhookPayload,
)

logger = logging.getLogger(__name__)


class TelegramStarsProvider(BasePaymentProvider):
    """
    Telegram Stars — sendInvoice создаётся в handler.
    Provider валидирует и возвращает данные для invoice.
    """

    @property
    def name(self) -> str:
        return "telegram_stars"

    async def create_payment(self, request: CreatePaymentRequest) -> PaymentResult:
        """
        Stars: handler вызывает sendInvoice. Возвращаем payload для invoice.
        """
        return PaymentResult(
            success=True,
            provider_payment_id=request.idempotency_key,
            invoice_payload=request.idempotency_key,
            metadata={"user_id": request.user_id, "payment_type": request.payment_type},
        )

    async def verify_webhook(
        self, payload: bytes, signature: str | None, headers: dict | None
    ) -> bool:
        """Telegram Update — проверяется токеном бота."""
        return True

    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse from successful_payment (handler passes pre-parsed)."""
        if "successful_payment" not in payload:
            return None
        sp = payload["successful_payment"]
        user_id = payload.get("from", {}).get("id") if isinstance(payload.get("from"), dict) else None
        user_id = user_id or payload.get("user_id")
        return WebhookPayload(
            provider_payment_id=sp.get("telegram_payment_charge_id", ""),
            status="succeeded",
            amount=Decimal(sp.get("total_amount", 0)) / 100,
            currency=sp.get("currency", "XTR"),
            user_id=int(user_id) if user_id else None,
            payment_type="balance_topup",
            metadata=payload,
        )
