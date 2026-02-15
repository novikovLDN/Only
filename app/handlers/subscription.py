"""Subscription and payment."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.core.enums import Tariff
from app.keyboards.inline import tariff_select, payment_method_select, back_only

router = Router(name="subscription")


@router.callback_query(F.data == "to_subscription")
async def to_subscription_cb(callback: CallbackQuery, user, t) -> None:
    await callback.message.edit_text(
        t("subscription.choose_tariff"),
        reply_markup=tariff_select(t),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff_"))
async def tariff_selected(callback: CallbackQuery, user, t) -> None:
    tariff_val = callback.data.replace("tariff_", "")
    try:
        Tariff(tariff_val)
    except ValueError:
        await callback.answer()
        return
    await callback.message.edit_text(
        t("subscription.choose_payment"),
        reply_markup=payment_method_select(t, tariff_val),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def payment_selected(callback: CallbackQuery, user, t, session) -> None:
    parts = callback.data.split("_", 2)
    if len(parts) < 3:
        await callback.answer()
        return
    provider = parts[1]
    tariff_val = parts[2]
    try:
        tariff = Tariff(tariff_val)
    except ValueError:
        await callback.answer()
        return
    from app.repositories.payment_repo import PaymentRepository
    from app.services.payment_service import PaymentService
    from app.repositories.user_repo import UserRepository

    pay_repo = PaymentRepository(session)
    user_repo = UserRepository(session)
    pay_svc = PaymentService(pay_repo, user_repo)
    payment = await pay_svc.create_payment(user, tariff, provider)
    await session.commit()
    await callback.message.edit_text(
        f"Invoice #{payment.id}, {payment.amount}₽ ({provider}) — stub",
        reply_markup=back_only(t, "to_subscription"),
    )
    await callback.answer()
