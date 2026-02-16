"""Payment service — YooKassa / Telegram."""

import logging
from datetime import datetime, timedelta, timezone

from aiogram.types import LabeledPrice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, Referral, User
from app.services.referral_service import give_reward_if_pending
from app.services.user_service import extend_premium

logger = logging.getLogger(__name__)

TARIFF_MONTHS = {1: 1, 3: 3, 6: 6, 12: 12}
TARIFF_NAMES = {1: "1m", 3: "3m", 6: "6m", 12: "12m"}
TARIFF_PRICES = {1: 19900, 3: 49900, 6: 79900, 12: 129900}


async def create_invoice(
    session: AsyncSession,
    bot,
    user: User,
    months: int,
    provider_token: str,
) -> Payment | None:
    """Create pending payment, send invoice, save message_id, schedule expire. Returns payment."""
    tariff = TARIFF_NAMES.get(months, "1m")
    amount = TARIFF_PRICES.get(months, 19900)
    p = Payment(
        user_id=user.id,
        tariff=tariff,
        amount=amount,
        provider="telegram",
        status="pending",
    )
    session.add(p)
    await session.flush()
    await session.refresh(p)

    try:
        prices = [LabeledPrice(label=f"{months} мес", amount=amount)]
        msg = await bot.send_invoice(
            chat_id=user.telegram_id,
            title="💎 Premium подписка",
            description=f"Оплата тарифа: {months} мес",
            payload=str(p.id),
            provider_token=provider_token,
            currency="RUB",
            prices=prices,
        )
        p.invoice_message_id = msg.message_id
        await session.commit()

        from app.scheduler import get_scheduler
        from app.services.payment_service import expire_payment
        sched = get_scheduler()
        run_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        sched.add_job(
            expire_payment,
            trigger="date",
            run_date=run_at,
            args=[p.id, user.telegram_id, msg.message_id, bot],
            id=f"expire_payment_{p.id}",
            replace_existing=True,
        )
        return p
    except Exception as e:
        logger.exception("Create invoice failed: %s", e)
        await session.rollback()
        return None


async def expire_payment(payment_id: int, tg_id: int, message_id: int, bot=None) -> None:
    """Mark payment expired and delete invoice message."""
    from app.db import get_session_maker
    sm = get_session_maker()
    async with sm() as session:
        payment = await session.get(Payment, payment_id)
        if payment and payment.status == "pending":
            payment.status = "expired"
            await session.commit()
    if bot:
        try:
            await bot.delete_message(chat_id=tg_id, message_id=message_id)
        except Exception as e:
            logger.warning("Expire: delete message failed: %s", e)


async def record_payment(
    session: AsyncSession,
    user_id: int,
    amount: int,
    tariff: str = "1m",
    provider: str = "telegram",
    external_payment_id: str | None = None,
    bot: "Bot | None" = None,
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

        ref_result = await session.execute(
            select(Referral).where(Referral.referral_user_id == user_id)
        )
        referral = ref_result.scalar_one_or_none()
        if referral:
            referrer = await give_reward_if_pending(session, referral)
            if referrer and bot:
                try:
                    from app.texts import t
                    lang = referrer.language_code if referrer.language_code in ("ru", "en") else "ru"
                    await bot.send_message(
                        chat_id=referrer.telegram_id,
                        text=t(lang, "referral_bonus_notify"),
                    )
                except Exception:
                    pass

    await session.refresh(p)
    return p
