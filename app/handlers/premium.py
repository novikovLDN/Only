"""Premium — tariffs, YooKassa Telegram Invoice."""

from aiogram import Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from app.db import get_session_maker
from app.config import settings
from app.keyboards import main_menu, premium_menu
from app.services import achievement_service, user_service
from app.utils.safe_edit import safe_edit_or_send
from app.texts import t

router = Router(name="premium")


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
    await safe_edit_or_send(cb, btn, reply_markup=premium_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("pay_"))
async def cb_pay(cb: CallbackQuery) -> None:
    await cb.answer()
    months = int(cb.data.replace("pay_", ""))
    tid = cb.from_user.id if cb.from_user else 0

    if not settings.payment_provider_token:
        await cb.message.answer("Payments not configured.")
        return

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        from app.services.payment_service import create_invoice
        payment = await create_invoice(
            session,
            cb.bot,
            user,
            months,
            settings.payment_provider_token,
        )
    if not payment:
        await cb.message.answer("Ошибка создания оплаты. Попробуйте позже.")


@router.pre_checkout_query()
async def pre_checkout_handler(pq: PreCheckoutQuery) -> None:
    await pq.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    sp = message.successful_payment
    if not sp:
        return
    try:
        payment_id = int(sp.invoice_payload)
    except (ValueError, TypeError):
        return

    sm = get_session_maker()
    async with sm() as session:
        from app.services.payment_service import TARIFF_NAMES, TARIFF_MONTHS
        from app.models import Payment, User, Referral
        from app.services.referral_service import give_reward_if_pending
        from sqlalchemy import select

        payment = await session.get(Payment, payment_id)
        if not payment or payment.status == "paid":
            return

        user = await session.get(User, payment.user_id)
        if not user:
            return

        months = 1
        for m, name in TARIFF_NAMES.items():
            if payment.tariff == name:
                months = m
                break
        was_premium = user_service.is_premium(user)
        await user_service.extend_premium(session, user, months)

        payment.status = "paid"
        payment.external_payment_id = sp.provider_payment_charge_id or None
        await session.flush()

        ref_result = await session.execute(
            select(Referral).where(Referral.referral_user_id == user.id)
        )
        referral = ref_result.scalar_one_or_none()
        if referral:
            referrer = await give_reward_if_pending(session, referral)
            if referrer:
                try:
                    lang = referrer.language_code if referrer.language_code in ("ru", "en") else "ru"
                    await message.bot.send_message(
                        chat_id=referrer.telegram_id,
                        text=t(lang, "referral_bonus_notify"),
                    )
                except Exception:
                    pass

        await session.commit()
        await achievement_service.check_achievements(
            session, user.id, user, message.bot, user.telegram_id, trigger="subscription_purchased"
        )
        await session.commit()
        if referral:
            referrer = await session.get(User, referral.referrer_id)
            if referrer:
                await achievement_service.check_achievements(
                    session, referrer.id, referrer, message.bot, referrer.telegram_id, trigger="friend_invited"
                )
                await session.commit()
        invoice_msg_id = payment.invoice_message_id

    if invoice_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=user.telegram_id,
                message_id=invoice_msg_id,
            )
        except Exception:
            pass

    lang = user.language_code
    text = t(lang, "premium_extended") if was_premium else t(lang, "premium_success")
    await message.answer(text, reply_markup=main_menu(lang, user_service.is_premium(user)))
