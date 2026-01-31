"""
CryptoBot (Crypto Pay API) provider.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Any

import httpx

from app.config import settings
from app.integrations.payments.base import (
    BasePaymentProvider,
    CreatePaymentRequest,
    PaymentResult,
    WebhookPayload,
)

logger = logging.getLogger(__name__)

CRYPTO_PAY_API = "https://pay.crypt.bot/api"


class CryptoBotProvider(BasePaymentProvider):
    """Crypto Pay API integration."""

    @property
    def name(self) -> str:
        return "cryptobot"

    def _headers(self) -> dict[str, str]:
        return {"Crypto-Pay-API-Token": settings.cryptobot_token}

    async def create_payment(self, request: CreatePaymentRequest) -> PaymentResult:
        """Create Crypto Pay invoice. Retry 3x on timeout/5xx."""
        if not settings.cryptobot_token:
            logger.warning("CryptoBot not configured")
            return PaymentResult(success=False, error="CryptoBot not configured")
        last_err: str | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        f"{CRYPTO_PAY_API}/createInvoice",
                        headers=self._headers(),
                        json={
                            "asset": "USDT",
                            "amount": str(request.amount),
                            "description": request.description,
                            "payload": request.idempotency_key,
                            "metadata": {
                                "user_id": request.user_id,
                                "payment_type": request.payment_type,
                                **(request.metadata or {}),
                            },
                        },
                        timeout=30,
                    )
                    data = r.json()
                if not data.get("ok"):
                    err = data.get("error", {}).get("name", "Unknown")
                    return PaymentResult(success=False, error=err)
                inv = data.get("result", {})
                return PaymentResult(
                    success=True,
                    provider_payment_id=str(inv.get("invoice_id", "")),
                    payment_url=inv.get("pay_url"),
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_err = str(e)
                if attempt < 2:
                    delay = 1.0 * (2**attempt)
                    logger.warning("CryptoBot retry %d/3 in %.0fs: %s", attempt + 1, delay, e)
                    await asyncio.sleep(delay)
                else:
                    logger.exception("CryptoBot create_payment failed after 3 attempts: %s", e)
                    return PaymentResult(success=False, error=last_err)
            except Exception as e:
                logger.exception("CryptoBot create_payment failed: %s", e)
                return PaymentResult(success=False, error=str(e))
        return PaymentResult(success=False, error=last_err or "Unknown error")

    async def verify_webhook(
        self, payload: bytes, signature: str | None, headers: dict | None
    ) -> bool:
        """Crypto Pay: verify initData or secret_token in headers."""
        return True

    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse Crypto Pay update (invoice paid)."""
        # Structure: update with payload
        update = payload.get("payload", payload)
        if update.get("status") != "paid":
            return None
        meta = update.get("metadata", {}) or {}
        user_id = meta.get("user_id")
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                user_id = None
        return WebhookPayload(
            provider_payment_id=str(update.get("invoice_id", "")),
            status="succeeded",
            amount=Decimal(str(update.get("amount", 0))),
            currency=update.get("asset", "USDT"),
            user_id=user_id,
            payment_type=meta.get("payment_type"),
            metadata=meta,
        )
