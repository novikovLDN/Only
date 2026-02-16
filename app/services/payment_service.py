"""Payment service — YooKassa / Telegram payments."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, User
from app.services.user_service import extend_premium
from app.services.referral_service import get_referral, give_reward_if_pending


TARIFF_MONTHS = {1: 1, 3: 3, 6: 6, 12: 12}


async def record_payment(
    session: AsyncSession,
    user_id: int,
    amount: int,
    provider_charge_id: str | None = None,
    telegram_charge_id: str | None = None,
) -> Payment:
    months = 1
    for m, price in [(1, 199), (3, 499), (6, 799), (12, 1299)]:
        if amount >= price:
            months = m
    p = Payment(
        user_id=user_id,
        amount=amount,
        provider_payment_charge_id=provider_charge_id,
        telegram_payment_charge_id=telegram_charge_id,
    )
    session.add(p)
    await session.flush()

    user = await session.get(User, user_id)
    if user:
        await extend_premium(session, user, months)
        # Check referral reward
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
