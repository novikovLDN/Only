"""
Base payment provider interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PaymentResult:
    """Result of payment creation."""

    success: bool
    payment_id: str | None = None
    payment_url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class WebhookPayload:
    """Parsed webhook payload."""

    provider_payment_id: str
    status: str
    amount: Decimal
    currency: str
    user_id: int | None = None
    metadata: dict[str, Any] | None = None


class BasePaymentProvider(ABC):
    """Abstract base for payment providers."""

    @abstractmethod
    async def create_payment(
        self,
        user_id: int,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Create payment and return URL or invoice."""

    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool:
        """Verify webhook signature."""

    @abstractmethod
    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse webhook body to WebhookPayload."""
