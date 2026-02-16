"""Habit creation FSM — presets, days, time, confirm."""

from datetime import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.core.habit_presets import get_preset_title
from app.keyboards.habits import build_presets_keyboard, weekdays_keyboard, time_keyboard, confirm_keyboard
from app.services import achievement_service, habit_service, user_service
from app.texts import t

router = Router(name="habits_create")


class CreateHabitStates(StatesGroup):
    preset = State()
    custom_title = State()
    days = State()
    time_slot = State()
    confirm = State()


@router.callback_query(F.data == "premium_required")
async def cb_premium_required(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "ru"
    await cb.message.edit_text(
        t(lang, "premium_required_upsell"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "btn_premium"), callback_data="premium")],
                [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="add_habit")],
            ]
        ),
    )


@router.callback_query(lambda c: c.data == "add_habit")
async def cb_add_habit(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        is_premium = user_service.is_premium(user)
        count = await habit_service.count_user_habits(session, user.id)
        if count >= 1 and not is_premium:
            await cb.message.edit_text(t(lang, "premium_paywall"), reply_markup=back_only(lang))
            return

    await state.set_state(CreateHabitStates.preset)
    await state.update_data(page=0, selected_preset=None, weekdays=[], times=[], lang=lang, is_premium=is_premium)

    kb = build_presets_keyboard(lang, is_premium, 0)
    await cb.message.edit_text(t(lang, "habit_presets"), reply_markup=kb)


@router.callback_query(CreateHabitStates.preset, lambda c: c.data and (c.data.startswith("preset_page_") or c.data.startswith("select_preset_") or c.data == "preset_custom"))
async def cb_preset_select(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    is_premium = data.get("is_premium", False)
    page = data.get("page", 0)
    tid = cb.from_user.id if cb.from_user else 0

    if cb.data and cb.data.startswith("preset_page_"):
        try:
            page = max(0, int(cb.data.split("_")[-1]))
        except (ValueError, IndexError):
            page = 0
        await state.update_data(page=page)
        kb = build_presets_keyboard(lang, is_premium, page)
        await cb.message.edit_text(t(lang, "habit_presets"), reply_markup=kb)
        return

    if cb.data == "preset_custom":
        if not is_premium:
            await cb.answer(t(lang, "premium_paywall"), show_alert=True)
            return
        await state.set_state(CreateHabitStates.custom_title)
        await state.update_data(custom=True)
        await cb.message.edit_text(t(lang, "habit_name_prompt"), reply_markup=back_only(lang))
        return

    if cb.data and cb.data.startswith("select_preset_"):
        try:
            preset_id = int(cb.data.split("_")[-1])
        except (ValueError, IndexError):
            return
        if not is_premium and preset_id > 3:
            await cb.answer(t(lang, "premium_locked_alert"), show_alert=True)
            return
        title = get_preset_title(preset_id, lang)
        if not title:
            return
        await state.update_data(selected_preset=title, habit_title=title, custom=False)
        await state.set_state(CreateHabitStates.days)

        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "ru"

        await cb.message.edit_text(t(lang, "habit_select_days"), reply_markup=weekdays_keyboard([], lang))


@router.callback_query(CreateHabitStates.days, lambda c: c.data and (c.data.startswith("wd_") or c.data == "days_ok"))
async def cb_days(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    weekdays = list(data.get("weekdays", []))
    tid = cb.from_user.id if cb.from_user else 0

    if cb.data == "days_ok":
        if not weekdays:
            return
        await state.update_data(weekdays=weekdays)
        await state.set_state(CreateHabitStates.time_slot)
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "en"
        await cb.message.edit_text(t(lang, "habit_select_time"), reply_markup=time_keyboard([], lang))
        return

    wd = int(cb.data.split("_")[1])
    if wd in weekdays:
        weekdays.remove(wd)
    else:
        weekdays.append(wd)
        weekdays.sort()
    await state.update_data(weekdays=weekdays)

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "habit_select_days"), reply_markup=weekdays_keyboard(weekdays, lang))


@router.callback_query(CreateHabitStates.time_slot, lambda c: c.data and (c.data.startswith("tm_") or c.data == "time_ok"))
async def cb_time(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    times = list(data.get("times", []))
    tid = cb.from_user.id if cb.from_user else 0

    if cb.data == "time_ok":
        if not times:
            return
        await state.update_data(times=times)
        await state.set_state(CreateHabitStates.confirm)
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid)
            lang = user.language_code if user else "en"
        title = data.get("habit_title", "")
        wd_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        days_str = ", ".join(wd_names[d] for d in sorted(data.get("weekdays", [])))
        times_str = ", ".join(sorted(times))
        text = f"{t(lang, 'habit_confirm')}\n\n{t(lang, 'habit_label')}: {title}\n{t(lang, 'days_label')}: {days_str}\n{t(lang, 'time_label')}: {times_str}"
        await cb.message.edit_text(text, reply_markup=confirm_keyboard(lang))
        return

    t_slot = cb.data.replace("tm_", "")
    if t_slot in times:
        times.remove(t_slot)
    else:
        times.append(t_slot)
        times.sort()
    await state.update_data(times=times)

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"

    await cb.message.edit_text(t(lang, "habit_select_time"), reply_markup=time_keyboard(times, lang))


@router.callback_query(CreateHabitStates.preset, lambda c: c.data == "back_main")
@router.callback_query(CreateHabitStates.days, lambda c: c.data == "back_main")
@router.callback_query(CreateHabitStates.time_slot, lambda c: c.data == "back_main")
@router.callback_query(CreateHabitStates.confirm, lambda c: c.data in ("back_main", "habit_cancel"))
async def cb_create_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.clear()
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        is_premium = user_service.is_premium(user) if user else False
    await cb.message.edit_text(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(CreateHabitStates.custom_title, lambda c: c.data == "back_main")
async def cb_custom_back(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.clear()
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        is_premium = user_service.is_premium(user) if user else False
    await cb.message.edit_text(
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.callback_query(CreateHabitStates.confirm, lambda c: c.data == "habit_confirm_ok")
async def cb_confirm_ok(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    title = data.get("habit_title", "")
    weekdays = data.get("weekdays", [])
    times = data.get("times", [])
    tid = cb.from_user.id if cb.from_user else 0

    if not title or not weekdays or not times:
        await state.clear()
        return

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        await habit_service.create(session, user.id, title, weekdays, times)
        await achievement_service.check_achievements(
            session, user.id, user, cb.bot, user.telegram_id
        )
        await session.commit()
        lang = user.language_code

    await state.clear()
    is_premium = user_service.is_premium(user)
    await cb.message.edit_text(
        t(lang, "habit_created"),
        reply_markup=main_menu(lang, is_premium),
    )


@router.message(CreateHabitStates.custom_title, F.text)
async def habit_custom_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()[:100]
    if not title:
        return
    await state.update_data(habit_title=title)
    await state.set_state(CreateHabitStates.days)
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
    await message.answer(t(lang, "habit_select_days"), reply_markup=weekdays_keyboard([], lang))
