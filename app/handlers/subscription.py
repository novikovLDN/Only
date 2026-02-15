"""Subscription and payment — inline keyboards only, Telegram Invoice / YooKassa."""

from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery

from app.keyboards.inline import main_menu, tariff_select

router = Router(name="subscription")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, session, user, t) -> None:
    payload = message.successful_payment.invoice_payload
    try:
        payment_id = int(payload)
    except (ValueError, TypeError):
        return
    from app.repositories.payment_repo import PaymentRepository
    from app.repositories.user_repo import UserRepository
    from app.services.payment_service import PaymentService

    pay_repo = PaymentRepository(session)
    user_repo = UserRepository(session)
    pay_svc = PaymentService(pay_repo, user_repo)
    await pay_svc.confirm_payment(payment_id)
    await message.answer(
        "🎉 Payment successful!\n\nYour subscription is now active.",
        reply_markup=main_menu(t),
    )
