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

    from app.services.discount_service import is_discount_active
    text = t(lang, "premium_screen")
    if is_discount_active(user):
        until_str = user.discount_until.strftime("%d.%m.%Y") if user.discount_until else ""
        text = text + "\n\n" + t(lang, "premium_discount_banner", percent=user.discount_percent, until=until_str)
    await safe_edit_or_send(cb, text, reply_markup=premium_menu(lang, user))


@router.callback_query(lambda c: c.data and c.data.startswith("buy_tariff:"))
async def cb_select_tariff(cb: CallbackQuery) -> None:
    """Tariff selected → show payment method (Card / Crypto)."""
    await cb.answer()
    tariff_code = (cb.data or "").split(":", 1)[1].strip()
    from app.core.premium import PREMIUM_TARIFFS
    if tariff_code not in PREMIUM_TARIFFS:
        return
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
    from app.keyboards.premium import payment_method_menu
    text = t(lang, "payment_method_prompt")
    await cb.message.edit_text(text, reply_markup=payment_method_menu(lang, tariff_code))


@router.callback_query(lambda c: c.data and c.data.startswith("pay_card:"))
async def cb_pay_card(cb: CallbackQuery) -> None:
    """Card selected → Telegram Invoice."""
    await cb.answer()
    tariff_code = (cb.data or "").split(":", 1)[1].strip()
    tid = cb.from_user.id if cb.from_user else 0
    if not settings.payment_provider_token:
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "ru"
        await cb.message.answer(t(lang, "premium_paywall"), reply_markup=main_menu(lang))
        return
    from app.core.premium import PREMIUM_TARIFFS
    if tariff_code not in PREMIUM_TARIFFS:
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
            tariff_code,
            settings.payment_provider_token,
        )
    if not payment:
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "ru"
        await cb.message.answer("Ошибка создания оплаты. Попробуйте позже.", reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("pay_crypto:"))
async def cb_pay_crypto(cb: CallbackQuery) -> None:
    """Crypto selected → show network selection."""
    await cb.answer()
    tariff_code = (cb.data or "").split(":", 1)[1].strip()
    tid = cb.from_user.id if cb.from_user else 0
    from app.core.premium import PREMIUM_TARIFFS
    if tariff_code not in PREMIUM_TARIFFS:
        return
    if not settings.crypto_api_key or not settings.webhook_base_url:
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "ru"
        await cb.message.answer("Crypto payments not configured.", reply_markup=main_menu(lang))
        return
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
    from app.keyboards.premium import crypto_network_menu
    text = t(lang, "crypto_network_select_prompt")
    await cb.message.edit_text(text, reply_markup=crypto_network_menu(lang, tariff_code))


@router.callback_query(lambda c: c.data and c.data.startswith("payment_method:"))
async def cb_payment_method_back(cb: CallbackQuery) -> None:
    """Back from network selection → payment method."""
    await cb.answer()
    tariff_code = (cb.data or "").split(":", 1)[1].strip()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
    from app.keyboards.premium import payment_method_menu
    text = t(lang, "payment_method_prompt")
    await cb.message.edit_text(text, reply_markup=payment_method_menu(lang, tariff_code))


@router.callback_query(lambda c: c.data and c.data.startswith("crypto_network_"))
async def cb_crypto_network(cb: CallbackQuery) -> None:
    """Network selected → create 2328 payment, send address + pay URL."""
    await cb.answer()
    parts = (cb.data or "").split(":")
    if len(parts) < 2:
        return
    network = parts[0].replace("crypto_network_", "")
    tariff_code = parts[1].strip()
    tid = cb.from_user.id if cb.from_user else 0
    from app.core.premium import PREMIUM_TARIFFS
    if tariff_code not in PREMIUM_TARIFFS:
        return
    from app.services.crypto_service import ALLOWED_NETWORKS, create_crypto_payment
    if network not in ALLOWED_NETWORKS:
        return
    if not settings.crypto_api_key or not settings.webhook_base_url:
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "ru"
        await cb.message.answer("Crypto payments not configured.", reply_markup=main_menu(lang))
        return
    import uuid
    order_id = f"CRYPTO-{tid}-{uuid.uuid4().hex[:8]}"
    url_callback = f"{settings.webhook_base_url.rstrip('/')}/webhook/crypto"
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        payment, pay_url = await create_crypto_payment(
            session,
            user,
            tariff_code,
            network,
            order_id,
            url_callback,
        )
        if payment:
            payment.invoice_message_id = cb.message.message_id if cb.message else None
        await session.commit()
    if not payment or not payment.crypto_address:
        await cb.message.answer("Ошибка создания крипто-оплаты. Попробуйте позже.", reply_markup=main_menu(lang))
        return
    # Use actual (discounted) amount from payment
    final_rub = payment.amount / 100  # amount is kopecks
    price_usd = round(final_rub / 100, 2)  # RUB->USD same as crypto_service
    from app.services.crypto_service import CURRENCY, NETWORK_LABELS
    network_label = NETWORK_LABELS.get(network, network)
    text = t(lang, "crypto_invoice_full", amount=price_usd, currency=CURRENCY, network=network_label, address=payment.crypto_address, network_short=network_label)
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if pay_url:
        pay_btn = t(lang, "crypto_pay_btn")
        kb.inline_keyboard = [[InlineKeyboardButton(text=pay_btn, url=pay_url)]]
    kb.inline_keyboard.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="premium")])
    await cb.message.edit_text(text, reply_markup=kb)


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
                    lang = referrer.language_code if referrer.language_code in ("ru", "en", "ar") else "ru"
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
