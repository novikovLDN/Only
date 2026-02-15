"""Payment service — Telegram Invoice / YooKassa."""

from datetime import datetime, timedelta, timezone

from app.core.models import Payment, User
from app.core.tariffs import TARIFFS
from app.repositories.payment_repo import PaymentRepository
from app.repositories.user_repo import UserRepository


class PaymentService:
    def __init__(self, payment_repo: PaymentRepository, user_repo: UserRepository):
        self.payment_repo = payment_repo
        self.user_repo = user_repo

    def get_tariff(self, tariff_key: str) -> dict | None:
        return TARIFFS.get(tariff_key)

    async def create_payment(self, user: User, tariff_key: str, provider: str = "card") -> Payment | None:
        tariff = TARIFFS.get(tariff_key)
        if not tariff:
            return None

        payment = await self.payment_repo.create(
            user_id=user.id,
            tariff=tariff_key,
            provider=provider,
            amount=tariff["price"],
        )
        session = self.payment_repo.session
        await session.commit()
        await session.refresh(payment)
        return payment

    async def confirm_payment(self, payment_id: int) -> bool:
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment or payment.status != "pending":
            return False

        tariff = TARIFFS.get(payment.tariff)
        if not tariff:
            return False

        payment.status = "succeeded"
        user = await self.user_repo.get_by_id(payment.user_id)
        if not user:
            return False

        now = datetime.now(timezone.utc)
        if user.subscription_until and user.subscription_until > now:
            base = user.subscription_until
        else:
            base = now
        user.subscription_until = base + timedelta(days=tariff["days"])

        session = self.payment_repo.session
        await session.commit()
        return True
