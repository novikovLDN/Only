"""Add habit flow — presets (pagination), custom, weekdays, times."""

import logging
from datetime import time as dt_time
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.constants import HABIT_PRESETS_LIMIT_FREE
from app.i18n.loader import get_presets, get_weekdays
from app.keyboards.inline import (
    presets_page,
    weekdays_select,
    times_select,
    main_menu,
    buy_subscription_only,
)
from app.fsm.states import AddHabitStates

logger = logging.getLogger(__name__)
router = Router(name="habits")


async def show_presets_screen(callback: CallbackQuery, user, t, is_premium: bool, page: int = 0, selected: frozenset | None = None, state: FSMContext | None = None) -> None:
    lang = user.language or "en"
    sel = set(selected or ())
    if state:
        await state.update_data(preset_page=page, preset_selected=list(sel))
        await state.set_state(AddHabitStates.presets)
    await callback.message.edit_text(
        t("select_preset_list"),
        reply_markup=presets_page(t, lang, page, sel, is_premium),
    )


@router.callback_query(F.data == "premium")
async def premium_locked(callback: CallbackQuery, user, t) -> None:
    await callback.message.edit_text(
        t("premium_required"),
        reply_markup=buy_subscription_only(t),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("preset_toggle_"))
async def preset_toggle(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    idx = int(callback.data.split("_")[2])
    if not is_premium and idx >= HABIT_PRESETS_LIMIT_FREE:
        await callback.answer()
        return
    data = await state.get_data()
    selected = set(data.get("preset_selected", []))
    page = data.get("preset_page", 0)
    if idx in selected:
        selected.discard(idx)
    else:
        selected.add(idx)
    await state.update_data(preset_selected=list(selected))
    lang = user.language or "en"
    await callback.message.edit_reply_markup(
        reply_markup=presets_page(t, lang, page, selected, is_premium),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("preset_page_"))
async def preset_page_nav(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    page = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected = set(data.get("preset_selected", []))
    await show_presets_screen(callback, user, t, is_premium, page, frozenset(selected), state)
    await callback.answer()


@router.callback_query(F.data == "preset_done")
async def preset_done(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("preset_selected", []))
    if not selected:
        await callback.answer(t("select_at_least_one_day"), show_alert=True)
        return
    lang = user.language or "en"
    presets = get_presets(lang)
    titles = [presets[i] for i in sorted(selected)]
    await state.update_data(habit_titles=titles, is_custom=False)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "en"
    await callback.message.edit_text(
        t("select_weekdays"),
        reply_markup=weekdays_select(t, set(), lang, "day", "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "custom_habit")
async def custom_habit_start(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    await state.update_data(habit_titles=[], is_custom=True)
    await state.set_state(AddHabitStates.custom_text)
    from app.keyboards.inline import back_only
    await callback.message.edit_text(
        t("enter_custom_habit"),
        reply_markup=back_only(t, "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("day_"))
async def day_toggle(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    days = set(data.get("selected_days", []))
    if idx in days:
        days.discard(idx)
    else:
        days.add(idx)
    await state.update_data(selected_days=list(days))
    lang = user.language or "en"
    await callback.message.edit_reply_markup(
        reply_markup=weekdays_select(t, days, lang, "day", "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "days_done")
async def days_done(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    data = await state.get_data()
    days = data.get("selected_days", [])
    if not days:
        await callback.answer(t("select_at_least_one_day"), show_alert=True)
        return
    days_sorted = sorted(set(days))
    await state.update_data(selected_days=days_sorted)
    await state.set_state(AddHabitStates.times)
    await callback.message.edit_text(
        t("select_time"),
        reply_markup=times_select(t, set(), "time", "times_done", "back_to_days"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def time_toggle(callback: CallbackQuery, t, state: FSMContext) -> None:
    h = int(callback.data.split("_")[1])
    data = await state.get_data()
    times_set = set(data.get("selected_times", []))
    if h in times_set:
        times_set.discard(h)
    else:
        times_set.add(h)
    await state.update_data(selected_times=list(times_set))
    await callback.message.edit_reply_markup(
        reply_markup=times_select(t, times_set, "time", "times_done", "back_to_days"),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_days")
async def back_to_days(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    data = await state.get_data()
    days = set(data.get("selected_days", []))
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "en"
    await callback.message.edit_text(
        t("select_weekdays"),
        reply_markup=weekdays_select(t, days, lang, "day", "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "times_done")
async def times_done(callback: CallbackQuery, user, t, session, state: FSMContext) -> None:
    data = await state.get_data()
    times_list = data.get("selected_times", [])
    if not times_list:
        await callback.answer(t("select_at_least_one_time"), show_alert=True)
        return
    titles = data.get("habit_titles", [])
    if not titles:
        await state.clear()
        await callback.message.edit_text(t("welcome", first_name=user.first_name or "User"), reply_markup=main_menu(t))
        await callback.answer()
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
    await callback.message.edit_text(
        t("welcome", first_name=user.first_name or "User"),
        reply_markup=main_menu(t),
    )
    await callback.answer()


@router.message(AddHabitStates.custom_text, F.text)
async def custom_habit_text(message: Message, user, t, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 1 or len(text) > 100:
        await message.answer(t("custom_habit_invalid"))
        return
    await state.update_data(habit_titles=[text], is_custom=True)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "en"
    await message.answer(
        t("select_weekdays"),
        reply_markup=weekdays_select(t, set(), lang, "day", "back_main"),
    )
