"""Subscription and payment handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.core.enums import Tariff, TARIFF_PRICES_RUB

router = Router(name="subscription")


@router.callback_query(F.data == "to_subscription")
async def to_subscription(callback: CallbackQuery, user, t) -> None:
    rows = []
    for tariff, price in TARIFF_PRICES_RUB.items():
        label = f"{tariff.value} — {price} RUB"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"buy_{tariff.value}")])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    await callback.message.edit_text(t("buy_subscription"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def buy_subscription(callback: CallbackQuery, user, t, session) -> None:
    tariff_val = callback.data[4:]
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
    payment = await pay_svc.create_payment(user, tariff, "cryptobot")
    await session.commit()
    await callback.message.answer(
        f"Invoice: {payment.id}, amount {payment.amount} RUB. "
        "Crypto Bot / Telegram Payments integration placeholder.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("back"), callback_data="back_main")],
        ]),
    )
    await callback.answer()
