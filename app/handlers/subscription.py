"""Subscription and payment — Reply keyboard only."""

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.core.enums import Tariff, TARIFF_PRICES_RUB
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
    try:
        tariff = Tariff(tariff_val)
    except ValueError:
        await state.clear()
        await message.answer(_welcome(t, user), reply_markup=main_menu(t))
        return
    text = (message.text or "").lower()
    provider = "cryptobot" if "crypto" in text else "card"
    from app.repositories.payment_repo import PaymentRepository
    from app.services.payment_service import PaymentService
    from app.repositories.user_repo import UserRepository

    pay_repo = PaymentRepository(session)
    user_repo = UserRepository(session)
    pay_svc = PaymentService(pay_repo, user_repo)
    payment = await pay_svc.create_payment(user, tariff, provider)
    await session.commit()
    await state.clear()
    await message.answer(
        f"Invoice #{payment.id}, {payment.amount}₽ ({provider}) — stub",
        reply_markup=main_menu(t),
    )


@router.message(StateFilter("subscription:payment"), F.text.in_(BTN_BACK))
async def payment_back(message: Message, t, state: FSMContext) -> None:
    await state.clear()
    await send_tariff_screen(message, t)


def _welcome(t, user) -> str:
    name = getattr(user, "first_name", None) or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
