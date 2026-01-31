"""
Payment repository.
"""

from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Payment data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Payment)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        """Get payment by idempotency key (for deduplication)."""
        result = await self._session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_provider_id(self, provider: str, provider_id: str) -> Payment | None:
        """Get payment by provider's payment ID."""
        result = await self._session.execute(
            select(Payment).where(
                and_(
                    Payment.provider == provider,
                    Payment.provider_payment_id == provider_id,
                )
            )
        )
        return result.scalar_one_or_none()
