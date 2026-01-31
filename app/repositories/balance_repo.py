"""
Balance repository.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.balance import Balance
from app.repositories.base import BaseRepository


class BalanceRepository(BaseRepository[Balance]):
    """Balance data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Balance)

    async def get_by_user(self, user_id: int) -> Balance | None:
        """Get balance for user."""
        result = await self._session.execute(select(Balance).where(Balance.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int, currency: str = "RUB") -> Balance:
        """Get or create balance for user."""
        bal = await self.get_by_user(user_id)
        if bal:
            return bal
        bal = Balance(user_id=user_id, amount=Decimal("0"), currency=currency)
        await self.add(bal)
        return bal
