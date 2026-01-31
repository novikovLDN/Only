"""
Base payment provider interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class CreatePaymentRequest:
    """Request to create payment."""

    user_id: int
    amount: Decimal
    currency: str
    idempotency_key: str
    description: str
    payment_type: str  # balance_topup | subscription
    metadata: dict[str, Any] | None = None


@dataclass
class PaymentResult:
    """Result of payment creation."""

    success: bool
    provider_payment_id: str | None = None
    payment_url: str | None = None
    invoice_payload: str | None = None  # For Telegram Stars
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
    payment_type: str | None = None
    metadata: dict[str, Any] | None = None


class BasePaymentProvider(ABC):
    """Abstract base for payment providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""

    @abstractmethod
    async def create_payment(self, request: CreatePaymentRequest) -> PaymentResult:
        """Create payment and return URL or invoice data."""

    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str | None, headers: dict | None) -> bool:
        """Verify webhook signature/authenticity."""

    @abstractmethod
    async def parse_webhook(self, payload: dict[str, Any]) -> WebhookPayload | None:
        """Parse webhook body to WebhookPayload. Return None if event should be ignored."""
