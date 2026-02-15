"""Callback handlers — all inline keyboard actions."""

from datetime import date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards.inline import (
    main_menu,
    settings_menu,
    language_select_with_back,
    profile_menu,
    progress_menu,
    loyalty_menu,
    tariff_select,
    payment_method_select,
    buy_subscription_only,
)
router = Router(name="callbacks")
SUPPORT_URL = "https://t.me/asc_support"


def _welcome(user, t) -> str:
    name = getattr(user, "first_name", None) or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


@router.callback_query(F.data == "back_main")
async def cb_back_main(cb: CallbackQuery, user, t, state: FSMContext | None) -> None:
    await cb.answer()
    if state:
        await state.clear()
    await cb.message.edit_text(_welcome(user, t), reply_markup=main_menu(t))


@router.callback_query(F.data == "add_habit")
async def cb_add_habit(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext | None) -> None:
    from app.fsm.states import AddHabitStates
    from app.handlers.habits import send_presets_screen
    await cb.answer()
    if state:
        await state.set_state(AddHabitStates.presets)
        await state.update_data(current_page=0, selected_habits=[])
    await send_presets_screen(cb, user, t, is_premium, page=0)


@router.callback_query(F.data == "edit_habits")
async def cb_edit_habits(cb: CallbackQuery, user, t, session) -> None:
    from app.handlers.edit_habits import send_edit_habits_screen
    await cb.answer()
    await cb.message.delete()
    await send_edit_habits_screen(cb.message, user, t, session)


@router.callback_query(F.data == "loyalty")
async def cb_loyalty(cb: CallbackQuery, user, t, session) -> None:
    from app.handlers.loyalty import build_loyalty_content
    await cb.answer()
    text, kb = await build_loyalty_content(user, t, session, cb.bot)
    await cb.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "settings")
async def cb_settings(cb: CallbackQuery, user, t) -> None:
    await cb.answer()
    await cb.message.edit_text(t("settings.title"), reply_markup=settings_menu(t))


@router.callback_query(F.data == "to_subscription")
async def cb_to_subscription(cb: CallbackQuery, t, state: FSMContext | None) -> None:
    from app.handlers.subscription import send_tariff_screen as _send_tariff
    await cb.answer()
    if state:
        await state.clear()
    await cb.message.edit_text(t("subscription.choose_tariff"), reply_markup=tariff_select(t))


@router.callback_query(F.data == "settings_profile")
async def cb_settings_profile(cb: CallbackQuery, user, t, session) -> None:
    from app.handlers.profile import build_profile_content
    await cb.answer()
    text, kb = await build_profile_content(user, t, session)
    await cb.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "settings_lang")
async def cb_settings_lang(cb: CallbackQuery, user, t, state: FSMContext) -> None:
    from app.utils.i18n import lang_select_prompt
    await cb.answer()
    await state.set_state("settings:language")
    await cb.message.edit_text(lang_select_prompt(), reply_markup=language_select_with_back(t, "back_main"))


@router.callback_query(F.data.startswith("lang_"))
async def cb_lang_selected(cb: CallbackQuery, user, t, session, user_service) -> None:
    from app.utils.i18n import t as i18n_t
    await cb.answer()
    data = cb.data or ""
    if data == "lang_ru" or data == "lang_ru_settings":
        lang = "ru"
    elif data == "lang_en" or data == "lang_en_settings":
        lang = "en"
    else:
        return
    await user_service.update_language(user, lang)
    await session.commit()
    user.language = lang
    _t = lambda k, **kw: i18n_t(lang, k, **kw)
    if "settings" in data:
        await cb.message.edit_text(_t("settings.title"), reply_markup=settings_menu(_t))
    else:
        await cb.message.edit_text(_welcome(user, _t), reply_markup=main_menu(_t))


@router.callback_query(F.data == "share_link")
async def cb_share_link(cb: CallbackQuery, user, t) -> None:
    await cb.answer()
    try:
        me = await cb.bot.get_me()
        username = me.username or "your_bot"
    except Exception:
        username = "your_bot"
    link = f"https://t.me/{username}?start=ref_{user.telegram_id}"
    await cb.message.edit_text(link, reply_markup=main_menu(t))


@router.callback_query(F.data == "loyalty_details")
async def cb_loyalty_details(cb: CallbackQuery, t) -> None:
    await cb.answer()
    await cb.message.edit_text(t("loyalty.info"), reply_markup=main_menu(t))


@router.callback_query(F.data == "profile_progress")
async def cb_profile_progress(cb: CallbackQuery, user, t, session) -> None:
    from app.services.progress_service import ProgressService
    from app.utils.i18n import get_month_name
    await cb.answer()
    progress_svc = ProgressService(session)
    now = date.today()
    success_count, total, days_list = await progress_svc.get_month_progress(user.id, now.year, now.month)
    lang = user.language if user.language in ("ru", "en") else "ru"
    month_name = get_month_name(lang, now.month)
    if total == 0 or not days_list:
        text = t("progress.title", month=month_name) + "\n\n" + t("progress.empty")
        has_missed = False
    else:
        filled = int(round(30 * success_count / total)) if total else 0
        bar = "█" * filled + "░" * (30 - filled)
        text = t("progress.title", month=month_name) + "\n\n" + f"[{bar}]\n\n" + t("progress.days_done", count=success_count, total=total) + "\n\n"
        text += t("progress.no_skips") if success_count == total else t("progress.has_skips")
        missed = await progress_svc.get_missed_habits(user.id, now.year, now.month)
        has_missed = bool(missed)
    await cb.message.edit_text(text, reply_markup=progress_menu(t, has_missed))


@router.callback_query(F.data == "profile_missed")
async def cb_profile_missed(cb: CallbackQuery, user, t, session) -> None:
    from app.services.progress_service import ProgressService
    from app.utils.i18n import format_date_short, reason_to_text
    await cb.answer()
    progress_svc = ProgressService(session)
    missed = await progress_svc.get_missed_habits(user.id, date.today().year, date.today().month)
    lang = user.language if user.language in ("ru", "en") else "ru"
    if not missed:
        text = t("progress.empty")
    else:
        lines = [f"{format_date_short(lang, d)} — {title} ({reason_to_text(lang, reason)})" for d, title, reason in missed]
        text = t("progress.my_missed") + "\n\n" + "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=progress_menu(t, False))


@router.callback_query(F.data.startswith("tariff_"))
async def cb_tariff(cb: CallbackQuery, t, state: FSMContext) -> None:
    await cb.answer()
    tariff_val = (cb.data or "").replace("tariff_", "")
    await state.update_data(selected_tariff=tariff_val)
    await state.set_state("subscription:payment")
    await cb.message.edit_text(t("subscription.choose_payment"), reply_markup=payment_method_select(t, tariff_val))


@router.callback_query(F.data.startswith("pay_card_"))
async def cb_pay_card(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.config import settings
    from app.core.tariffs import TARIFFS, CURRENCY
    from app.repositories.payment_repo import PaymentRepository
    from app.repositories.user_repo import UserRepository
    from app.services.payment_service import PaymentService
    from aiogram.types import LabeledPrice
    await cb.answer()
    tariff_val = (cb.data or "").replace("pay_card_", "")
    tariff_cfg = TARIFFS.get(tariff_val)
    if not tariff_cfg:
        await state.clear()
        await cb.message.edit_text(_welcome(user, t), reply_markup=main_menu(t))
        return
    if not settings.payment_provider_token:
        await cb.message.edit_text("💳 Configure PAYMENT_PROVIDER_TOKEN (YooKassa) in Railway for card payments.", reply_markup=main_menu(t))
        await state.clear()
        return
    pay_repo = PaymentRepository(session)
    user_repo = UserRepository(session)
    pay_svc = PaymentService(pay_repo, user_repo)
    payment = await pay_svc.create_payment(user, tariff_val, "card")
    if not payment:
        await cb.message.edit_text(t("subscription.choose_payment"), reply_markup=payment_method_select(t, tariff_val))
        return
    prices = [LabeledPrice(label=tariff_cfg["title"], amount=tariff_cfg["price"] * 100)]
    await cb.bot.send_invoice(
        chat_id=cb.message.chat.id,
        title=f"Subscription — {tariff_cfg['title']}",
        description="Premium habit tracking access",
        payload=str(payment.id),
        provider_token=settings.payment_provider_token,
        currency=CURRENCY,
        prices=prices,
        need_email=False,
    )
    await state.clear()


@router.callback_query(F.data.startswith("pay_cryptobot_"))
async def cb_pay_cryptobot(cb: CallbackQuery, t) -> None:
    await cb.answer()
    await cb.message.edit_text("💎 CryptoBot — coming soon.", reply_markup=main_menu(t))


@router.callback_query(F.data == "premium")
async def cb_premium(cb: CallbackQuery, t) -> None:
    await cb.answer()
    await cb.message.edit_text(t("premium.block"), reply_markup=buy_subscription_only(t))


@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery) -> None:
    await cb.answer()
