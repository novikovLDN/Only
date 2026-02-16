"""Payments — Telegram Invoice."""

from aiogram import Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import settings
from app.db import get_session_maker
from app.keyboards import main_menu, subscription_menu
from app.services import achievement_service
from app.services.payments import TARIFF_DAYS, extend_subscription, get_days_from_payload
from app.texts import t
from sqlalchemy import select
from app.models import User

router = Router(name="payments")

PRICES = {"1": 19900, "3": 49900, "12": 99900}


@router.callback_query(lambda c: c.data == "subscription")
async def cb_subscription(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await cb.message.edit_text(t(lang, "btn_subscription"), reply_markup=subscription_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("pay_"))
async def cb_pay(cb: CallbackQuery) -> None:
    await cb.answer()
    tariff = cb.data.replace("pay_", "")
    days = TARIFF_DAYS.get(tariff, 30)
    amount = PRICES.get(tariff, 19900)

    tid = cb.from_user.id if cb.from_user else 0
    chat_id = cb.message.chat.id if cb.message else tid

    if not settings.payment_provider_token:
        sm = get_session_maker()
        async with sm() as session:
            r = await session.execute(select(User).where(User.telegram_id == tid))
            user = r.scalar_one_or_none()
            lang = user.language_code if user else "en"
        await cb.message.edit_text("Configure PAYMENT_PROVIDER_TOKEN", reply_markup=main_menu(lang))
        return

    await cb.bot.send_invoice(
        chat_id=chat_id,
        title="Premium Subscription",
        description=f"Access all features — {days} days",
        payload=f"sub_{tariff}_month",
        provider_token=settings.payment_provider_token,
        currency="RUB",
        prices=[LabeledPrice(label=f"{days} days", amount=amount)],
        need_email=False,
    )


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    tid = message.from_user.id if message.from_user else 0

    days = get_days_from_payload(payload)
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if user:
            await extend_subscription(session, user.id, days)
            await achievement_service.check_achievements(
                session, user.id, user, message.bot, user.telegram_id
            )
            await session.commit()
        lang = user.language_code if user else "en"

    await message.answer(t(lang, "premium_success"), reply_markup=main_menu(lang))


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery) -> None:
    await pre_checkout.answer(ok=True)
