"""Payment service — YooKassa / Telegram."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, User
from app.services.referral_service import give_reward_if_pending
from app.services.user_service import extend_premium

TARIFF_MONTHS = {1: 1, 3: 3, 6: 6, 12: 12}
TARIFF_NAMES = {1: "1m", 3: "3m", 6: "6m", 12: "12m"}


async def record_payment(
    session: AsyncSession,
    user_id: int,
    amount: int,
    tariff: str = "1m",
    provider: str = "telegram",
    external_payment_id: str | None = None,
) -> Payment:
    months = 1
    for m, name in TARIFF_NAMES.items():
        if tariff == name:
            months = m
            break

    p = Payment(
        user_id=user_id,
        tariff=tariff,
        amount=amount,
        provider=provider,
        external_payment_id=external_payment_id,
        status="completed",
    )
    session.add(p)
    await session.flush()

    user = await session.get(User, user_id)
    if user:
        await extend_premium(session, user, months)
        from sqlalchemy import select
        from app.models import Referral
        ref_result = await session.execute(
            select(Referral).where(Referral.referral_user_id == user_id)
        )
        referral = ref_result.scalar_one_or_none()
        if referral:
            await give_reward_if_pending(session, referral)

    await session.refresh(p)
    return p
