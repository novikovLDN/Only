"""Premium — tariffs, YooKassa."""

from aiogram import Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.db import get_session_maker
from app.config import settings
from app.keyboards import main_menu, premium_menu
from app.services import user_service
from app.texts import t

router = Router(name="premium")

TARIFFS = {1: 199, 3: 499, 6: 799, 12: 1299}


@router.callback_query(lambda c: c.data == "premium")
async def cb_premium(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        is_premium = user_service.is_premium(user)

    btn = t(lang, "btn_premium_extend") if is_premium else t(lang, "btn_premium")
    await cb.message.edit_text(btn, reply_markup=premium_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("pay_"))
async def cb_pay(cb: CallbackQuery) -> None:
    await cb.answer()
    months = int(cb.data.replace("pay_", ""))
    amount = TARIFFS.get(months, 199) * 100  # kopecks
    tid = cb.from_user.id if cb.from_user else 0

    if not settings.payment_provider_token:
        await cb.message.answer("Payments not configured.")
        return

    from aiogram import Bot
    bot = cb.bot
    await bot.send_invoice(
        chat_id=cb.message.chat.id,
        title="Premium Subscription",
        description=f"{months} month(s)",
        payload=f"premium_{months}",
        provider_token=settings.payment_provider_token,
        currency="RUB",
        prices=[LabeledPrice(label=f"{months} мес", amount=amount)],
    )


@router.pre_checkout_query()
async def pre_checkout_handler(pq: PreCheckoutQuery) -> None:
    await pq.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    tid = message.from_user.id if message.from_user else 0
    payload = (message.successful_payment or {}).invoice_payload
    months = 1
    if payload and payload.startswith("premium_"):
        try:
            months = int(payload.split("_")[1])
        except (IndexError, ValueError):
            pass

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        was_premium = user_service.is_premium(user)
        from app.services.payment_service import record_payment
        sp = message.successful_payment
        amount = (sp.total_amount or 0) if sp else 0
        ext_id = (sp.provider_payment_charge_id or "") if sp else ""
        tariff = f"{months}m"
        await record_payment(
            session,
            user.id,
            amount,
            tariff=tariff,
            provider="telegram",
            external_payment_id=ext_id or None,
            bot=message.bot,
        )
        await session.commit()

    text = t(lang, "premium_extended") if was_premium else t(lang, "premium_success")
    await message.answer(text, reply_markup=main_menu(lang, user_service.is_premium(user)))
