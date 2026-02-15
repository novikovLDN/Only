"""Payment service."""

from app.core.enums import PaymentStatus, Tariff, TARIFF_DAYS, TARIFF_PRICES_RUB
from app.core.models import Payment, User
from app.repositories.payment_repo import PaymentRepository
from app.repositories.user_repo import UserRepository


class PaymentService:
    def __init__(self, payment_repo: PaymentRepository, user_repo: UserRepository):
        self.payment_repo = payment_repo
        self.user_repo = user_repo

    def get_price_rub(self, tariff: Tariff) -> int:
        return TARIFF_PRICES_RUB[tariff]

    def get_days(self, tariff: Tariff) -> int:
        return TARIFF_DAYS[tariff]

    async def create_payment(
        self,
        user: User,
        tariff: Tariff,
        provider: str,
    ) -> Payment:
        amount = self.get_price_rub(tariff)
        return await self.payment_repo.create(
            user.id, tariff.value, provider, amount
        )

    async def mark_succeeded(self, payment: Payment) -> None:
        payment.status = PaymentStatus.SUCCEEDED.value
        tariff = Tariff(payment.tariff)
        days = TARIFF_DAYS[tariff]
        user = await self.user_repo.get_by_id(payment.user_id)
        if user:
            await self.user_repo.extend_subscription(user, days)
