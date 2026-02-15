"""Subscription and payment — Telegram Invoice / YooKassa."""

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice

from app.config import settings
from app.core.enums import Tariff, TARIFF_PRICES_RUB
from app.core.tariffs import TARIFFS, CURRENCY
from app.keyboards.reply import tariff_select, payment_method_select, main_menu
from app.utils.i18n import TRANSLATIONS, t as i18n_t

router = Router(name="subscription")

BTN_BACK = ("🔙 Back", "🔙 Назад")
TARIFF_KEYS = {"1_month": "subscription.tariff_1m", "3_months": "subscription.tariff_3m",
               "6_months": "subscription.tariff_6m", "12_months": "subscription.tariff_12m"}


def _tariff_labels() -> set:
    s = set()
    for lang in ("ru", "en"):
        for tariff, price in TARIFF_PRICES_RUB.items():
            key = TARIFF_KEYS.get(tariff.value, "subscription.tariff_1m")
            s.add(i18n_t(lang, key, price=price))
    return s

def _payment_labels() -> set:
    s = set()
    for lang in ("ru", "en"):
        t = TRANSLATIONS.get(lang, {})
        s.add(t.get("subscription.cryptobot", ""))
        s.add(t.get("subscription.bank_card", ""))
    return s

TARIFF_TEXTS = _tariff_labels()
PAYMENT_TEXTS = _payment_labels()


async def send_tariff_screen(message: Message, t) -> None:
    await message.answer(
        t("subscription.choose_tariff"),
        reply_markup=tariff_select(t),
    )


def _text_to_tariff(text: str) -> Tariff | None:
    for lang in ("ru", "en"):
        for tariff, price in TARIFF_PRICES_RUB.items():
            key = TARIFF_KEYS.get(tariff.value, "subscription.tariff_1m")
            if i18n_t(lang, key, price=price) == text:
                return tariff
    return None


@router.message(F.text.in_(TARIFF_TEXTS))
async def tariff_selected(message: Message, user, t, state: FSMContext) -> None:
    tariff = _text_to_tariff(message.text or "")
    if not tariff:
        return
    await state.update_data(selected_tariff=tariff.value)
    await state.set_state("subscription:payment")
    await message.answer(
        t("subscription.choose_payment"),
        reply_markup=payment_method_select(t, tariff.value),
    )


@router.message(F.text.in_(PAYMENT_TEXTS))
async def payment_selected(message: Message, user, t, session, state: FSMContext) -> None:
    if await state.get_state() != "subscription:payment":
        return
    data = await state.get_data()
    tariff_val = data.get("selected_tariff", "1_month")
    tariff_cfg = TARIFFS.get(tariff_val)
    if not tariff_cfg:
        await state.clear()
        await message.answer(_welcome(t, user), reply_markup=main_menu(t))
        return

    text = (message.text or "").lower()
    is_card = "bank" in text or "card" in text or "банков" in text or "карт" in text

    if is_card and settings.payment_provider_token:
        from app.repositories.payment_repo import PaymentRepository
        from app.services.payment_service import PaymentService
        from app.repositories.user_repo import UserRepository

        pay_repo = PaymentRepository(session)
        user_repo = UserRepository(session)
        pay_svc = PaymentService(pay_repo, user_repo)
        payment = await pay_svc.create_payment(user, tariff_val, "card")
        if not payment:
            await message.answer(t("subscription.choose_payment"), reply_markup=payment_method_select(t, tariff_val))
            return

        prices = [
            LabeledPrice(
                label=tariff_cfg["title"],
                amount=tariff_cfg["price"] * 100,
            )
        ]
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Subscription — {tariff_cfg['title']}",
            description="Premium habit tracking access",
            payload=str(payment.id),
            provider_token=settings.payment_provider_token,
            currency=CURRENCY,
            prices=prices,
            need_email=False,
        )
        await state.clear()
    else:
        if is_card:
            msg = "💳 Configure PAYMENT_PROVIDER_TOKEN (YooKassa) in Railway for card payments."
        else:
            msg = "💎 CryptoBot — coming soon."
        await message.answer(msg, reply_markup=main_menu(t))
        await state.clear()


@router.message(StateFilter("subscription:payment"), F.text.in_(BTN_BACK))
async def payment_back(message: Message, t, state: FSMContext) -> None:
    await state.clear()
    await send_tariff_screen(message, t)


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


def _welcome(t, user) -> str:
    name = getattr(user, "first_name", None) or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
