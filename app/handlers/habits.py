"""Add habit flow — inline keyboards only."""

import logging
from datetime import time as dt_time

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import (
    presets_page,
    weekdays_select,
    times_select,
    main_menu,
    buy_subscription_only,
)
from app.utils.i18n import get_presets, get_weekdays
from app.fsm.states import AddHabitStates
from app.core.constants import HABIT_PRESETS_LIMIT_FREE

logger = logging.getLogger(__name__)
router = Router(name="habits")


def _habit_text(t) -> str:
    return t("preset.choose_title") + "\n\n" + t("preset.choose_subtitle")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


async def send_presets_screen(
    msg_or_cb, user, t, is_premium: bool, page: int = 0,
    selected: set | None = None, state: FSMContext | None = None,
) -> None:
    lang = user.language or "ru"
    sel = selected or set()
    if state:
        await state.update_data(selected_habits=list(sel), current_page=page)
        await state.set_state(AddHabitStates.presets)
    presets = get_presets(lang)
    selected_titles = [presets[i] for i in sorted(sel)] if sel else []
    extra = f"\n\n✅ {t('preset.select_at_least_one').split('.')[0]}: {', '.join(selected_titles)}" if selected_titles else ""
    text = _habit_text(t) + extra
    kb = presets_page(t, lang, page, sel, is_premium)
    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.message.edit_text(text, reply_markup=kb)
    else:
        await msg_or_cb.answer(text, reply_markup=kb)


@router.callback_query(StateFilter(AddHabitStates.presets), F.data.startswith("habit_toggle:"))
async def cb_habit_toggle(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    hid = int((cb.data or "").split(":")[1])
    if not is_premium and hid >= HABIT_PRESETS_LIMIT_FREE:
        await cb.message.edit_text(t("premium.block"), reply_markup=buy_subscription_only(t))
        return
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    page = data.get("current_page", 0)
    if hid in selected:
        selected.discard(hid)
    else:
        selected.add(hid)
    await send_presets_screen(cb, user, t, is_premium, page, selected, state)


@router.callback_query(StateFilter(AddHabitStates.presets), F.data.startswith("habit_page:"))
async def cb_habit_page(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    page = int((cb.data or "").split(":")[1])
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    await send_presets_screen(cb, user, t, is_premium, page, selected, state)


@router.callback_query(StateFilter(AddHabitStates.presets), F.data == "habit_back")
async def cb_habit_back(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    page = data.get("current_page", 0)
    if page == 0:
        await state.clear()
        await cb.message.edit_text(_welcome(user, t), reply_markup=main_menu(t))
    else:
        selected = set(data.get("selected_habits", []))
        await send_presets_screen(cb, user, t, is_premium, page - 1, selected, state)


@router.callback_query(StateFilter(AddHabitStates.presets), F.data == "habit_next")
async def cb_habit_next(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    lang = user.language or "ru"
    presets = get_presets(lang)
    if not selected:
        page = data.get("current_page", 0)
        await cb.message.edit_text(t("preset.select_at_least_one") + "\n\n" + _habit_text(t), reply_markup=presets_page(t, lang, page, selected, is_premium))
        return
    titles = [presets[i] for i in sorted(selected)]
    await state.update_data(habit_titles=titles, is_custom=False)
    await state.set_state(AddHabitStates.weekdays)
    await cb.message.edit_text(t("preset.select_weekdays"), reply_markup=weekdays_select(t, selected, lang, "day", "habit_back_presets"))


@router.callback_query(StateFilter(AddHabitStates.presets), F.data == "custom_habit")
async def cb_custom_habit(cb: CallbackQuery, user, t, state: FSMContext) -> None:
    await cb.answer()
    await state.update_data(habit_titles=[], is_custom=True)
    await state.set_state(AddHabitStates.custom_text)
    await cb.message.edit_text(t("preset.enter_custom"), reply_markup=main_menu(t))


@router.callback_query(StateFilter(AddHabitStates.weekdays), F.data == "habit_back_presets")
async def cb_weekdays_back(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(AddHabitStates.presets)
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    page = data.get("current_page", 0)
    await send_presets_screen(cb, user, t, is_premium, page, selected, state)


@router.message(StateFilter(AddHabitStates.custom_text), F.text)
async def custom_habit_text(message: Message, user, t, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 1 or len(text) > 100:
        await message.answer(t("preset.custom_invalid"), reply_markup=main_menu(t))
        return
    await state.update_data(habit_titles=[text], is_custom=True)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "ru"
    await message.answer(t("preset.select_weekdays"), reply_markup=weekdays_select(t, set(), lang, "day", "habit_back_presets"))


@router.callback_query(StateFilter(AddHabitStates.weekdays), F.data.startswith("day_"))
async def cb_day(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    idx = int((cb.data or "").split("_")[1])
    data = await state.get_data()
    days = set(data.get("selected_days", []))
    if idx in days:
        days.discard(idx)
    else:
        days.add(idx)
    await state.update_data(selected_days=list(days))
    lang = user.language or "ru"
    weekdays = get_weekdays(lang)
    sel_str = ", ".join(weekdays[i] for i in sorted(days)) if days else ""
    extra = f"\n\n✅ {sel_str}" if sel_str else ""
    await cb.message.edit_text(t("preset.select_weekdays") + extra, reply_markup=weekdays_select(t, days, lang, "day", "habit_back_main"))


@router.callback_query(StateFilter(AddHabitStates.weekdays), F.data == "days_done")
async def cb_days_done(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    days = data.get("selected_days", [])
    lang = user.language or "ru"
    if not days:
        await cb.message.edit_text(t("preset.select_day") + "\n\n" + t("preset.select_weekdays"), reply_markup=weekdays_select(t, set(), lang, "day", "habit_back_presets"))
        return
    days_sorted = sorted(set(days))
    await state.update_data(selected_days=days_sorted)
    await state.set_state(AddHabitStates.times)
    await cb.message.edit_text(t("preset.select_time"), reply_markup=times_select(t, set(), "time", "times_done", "times_back"))


@router.callback_query(StateFilter(AddHabitStates.times), F.data.startswith("time_"))
async def cb_time(cb: CallbackQuery, user, t, state: FSMContext) -> None:
    await cb.answer()
    h = int((cb.data or "").split("_")[1])
    data = await state.get_data()
    times_set = set(data.get("selected_times", []))
    if h in times_set:
        times_set.discard(h)
    else:
        times_set.add(h)
    await state.update_data(selected_times=list(times_set))
    await cb.message.edit_text(t("preset.select_time"), reply_markup=times_select(t, times_set, "time", "times_done", "times_back"))


@router.callback_query(StateFilter(AddHabitStates.times), F.data == "times_done")
async def cb_times_done(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    await cb.answer()
    data = await state.get_data()
    times_list = data.get("selected_times", [])
    if not times_list:
        await cb.message.edit_text(t("preset.select_time_at_least") + "\n\n" + t("preset.select_time"), reply_markup=times_select(t, set(), "time", "times_done", "times_back"))
        return
    titles = data.get("habit_titles", [])
    if not titles:
        await state.clear()
        await cb.message.edit_text(_welcome(user, t), reply_markup=main_menu(t))
        return
    from app.repositories.habit_repo import HabitRepository
    from app.services.habit_service import HabitService
    from app.repositories.user_repo import UserRepository

    days = sorted(set(data.get("selected_days", [])))
    times_dt = [dt_time(h, 0) for h in sorted(set(times_list))]
    habit_repo = HabitRepository(session)
    user_repo = UserRepository(session)
    habit_svc = HabitService(habit_repo, user_repo)
    for title in titles:
        await habit_svc.create_habit(user, title, data.get("is_custom", False), days, times_dt)
    await session.commit()
    await state.clear()
    await cb.message.edit_text(_welcome(user, t), reply_markup=main_menu(t))


@router.callback_query(StateFilter(AddHabitStates.times), F.data == "times_back")
async def cb_times_back(cb: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(AddHabitStates.weekdays)
    data = await state.get_data()
    days = set(data.get("selected_days", []))
    lang = user.language or "ru"
    await cb.message.edit_text(t("preset.select_weekdays"), reply_markup=weekdays_select(t, days, lang, "day", "habit_back_presets"))
