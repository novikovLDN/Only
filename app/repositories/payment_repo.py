"""Payment repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        tariff: str,
        provider: str,
        amount: int,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            tariff=tariff,
            provider=provider,
            amount=amount,
            status="pending",
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: int) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()
