"""Telegram commands — full navigation. Always clear FSM, always message.answer()."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db import get_session_maker
from app.handlers.profile import _send_profile
from app.keyboards import back_only, main_menu
from app.keyboards.habits import build_presets_keyboard, habits_list
from app.keyboards.premium import premium_menu
from app.keyboards.profile import profile_keyboard
from app.keyboards.settings import settings_menu
from app.services import habit_service, referral_service, user_service
from app.texts import t

router = Router(name="commands")


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            await message.answer(t("ru", "main_greeting").format(name="there"), reply_markup=main_menu("ru", False))
            return
        lang = user.language_code
        is_premium = user_service.is_premium(user)
        count = await habit_service.count_user_habits(session, user.id)
        if count >= 1 and not is_premium:
            await message.answer(t(lang, "premium_paywall"), reply_markup=back_only(lang))
            return

    from app.handlers.habits_create import CreateHabitStates
    await state.set_state(CreateHabitStates.preset)
    await state.update_data(page=0, selected_preset=None, weekdays=[], times=[], lang=lang, is_premium=is_premium)

    await message.answer(
        t(lang, "habit_presets"),
        reply_markup=build_presets_keyboard(lang, is_premium, 0),
    )


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        habits = await habit_service.get_user_habits(session, user.id)

    if not habits:
        await message.answer(t(lang, "btn_edit_habits") + "\n\n" + t(lang, "edit_no_habits"), reply_markup=back_only(lang))
        return

    hs = [(h.id, h.title) for h in habits]
    await message.answer(t(lang, "btn_edit_habits"), reply_markup=habits_list(hs, lang))


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    fname = message.from_user.first_name if message.from_user else ""

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        ref_count = await referral_service.count_referrals(session, user.id)

    is_premium = user_service.is_premium(user)
    await _send_profile(message, user, ref_count, fname or "", lang, is_premium)


@router.message(Command("premium"))
async def cmd_premium(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        is_premium = user_service.is_premium(user)

    btn = t(lang, "btn_premium_extend") if is_premium else t(lang, "btn_premium")
    await message.answer(btn, reply_markup=premium_menu(lang))


@router.message(Command("referral"))
async def cmd_referral(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code

    bot_info = await message.bot.get_me()
    username = bot_info.username or "YourBot"
    link = f"https://t.me/{username}?start=ref_{user.id}"

    text = t(lang, "loyalty_title") + "\n\n" + t(lang, "loyalty_link") + "\n" + link
    await message.answer(text, reply_markup=back_only(lang))


@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext) -> None:
    await state.clear()
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "ru"

    await message.answer(t(lang, "settings_menu"), reply_markup=settings_menu(lang))
