"""Add habit flow."""

import logging
from datetime import time as dt_time

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.i18n.loader import get_presets
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


def _habit_text(t) -> str:
    return t("preset.choose_title") + "\n\n" + t("preset.choose_subtitle")


@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery) -> None:
    await callback.answer()


async def show_presets_screen(callback: CallbackQuery, user, t, is_premium: bool, page: int = 0, selected: frozenset | None = None, state: FSMContext | None = None) -> None:
    lang = user.language or "en"
    sel = set(selected or ())
    if state:
        await state.update_data(selected_habits=list(sel), current_page=page)
        await state.set_state(AddHabitStates.presets)
    try:
        await callback.message.edit_text(
            _habit_text(t),
            reply_markup=presets_page(t, lang, page, sel, is_premium),
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise


@router.callback_query(F.data == "premium")
async def premium_locked(callback: CallbackQuery, user, t) -> None:
    await callback.message.edit_text(
        t("premium.block"),
        reply_markup=buy_subscription_only(t),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("habit_toggle:"))
async def habit_toggle(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    try:
        idx = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    from app.core.constants import HABIT_PRESETS_LIMIT_FREE
    if not is_premium and idx >= HABIT_PRESETS_LIMIT_FREE:
        await callback.answer()
        return
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    page = data.get("current_page", 0)
    if idx in selected:
        selected.discard(idx)
    else:
        selected.add(idx)
    await state.update_data(selected_habits=list(selected))
    lang = user.language or "en"
    try:
        await callback.message.edit_reply_markup(
            reply_markup=presets_page(t, lang, page, selected, is_premium),
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("habit_page:"))
async def habit_page_nav(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    try:
        page = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    lang = user.language or "en"
    presets = get_presets(lang)
    total_pages = max(1, (len(presets) + 5) // 6)
    page = max(0, min(page, total_pages - 1))
    await state.update_data(current_page=page)
    try:
        await callback.message.edit_text(
            _habit_text(t),
            reply_markup=presets_page(t, lang, page, selected, is_premium),
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    await callback.answer()


@router.callback_query(F.data == "habit_back")
async def habit_back(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    if state:
        await state.clear()
    name = user.first_name or "User"
    text = t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
    await callback.message.edit_text(text, reply_markup=main_menu(t))
    await callback.answer()


@router.callback_query(F.data == "habit_next")
async def habit_next(callback: CallbackQuery, user, t, is_premium: bool, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("selected_habits", []))
    if not selected:
        await callback.answer(t("preset.select_at_least_one"), show_alert=True)
        return
    lang = user.language or "en"
    presets = get_presets(lang)
    titles = [presets[i] for i in sorted(selected)]
    await state.update_data(habit_titles=titles, is_custom=False)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "en"
    await callback.message.edit_text(
        t("preset.select_weekdays"),
        reply_markup=weekdays_select(t, set(), lang, "day", "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "custom_habit")
async def custom_habit_start(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    from app.keyboards.inline import back_only

    await state.update_data(habit_titles=[], is_custom=True)
    await state.set_state(AddHabitStates.custom_text)
    await callback.message.edit_text(
        t("preset.enter_custom"),
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
        await callback.answer(t("preset.select_day"), show_alert=True)
        return
    days_sorted = sorted(set(days))
    await state.update_data(selected_days=days_sorted)
    await state.set_state(AddHabitStates.times)
    await callback.message.edit_text(
        t("preset.select_time"),
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
        t("preset.select_weekdays"),
        reply_markup=weekdays_select(t, days, lang, "day", "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "times_done")
async def times_done(callback: CallbackQuery, user, t, session, state: FSMContext) -> None:
    data = await state.get_data()
    times_list = data.get("selected_times", [])
    if not times_list:
        await callback.answer(t("preset.select_time_at_least"), show_alert=True)
        return
    titles = data.get("habit_titles", [])
    if not titles:
        await state.clear()
        name = user.first_name or "User"
        await callback.message.edit_text(
            t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
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
    name = user.first_name or "User"
    await callback.message.edit_text(
        t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
        reply_markup=main_menu(t),
    )
    await callback.answer()


@router.message(AddHabitStates.custom_text, F.text)
async def custom_habit_text(message: Message, user, t, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 1 or len(text) > 100:
        await message.answer(t("preset.custom_invalid"))
        return
    await state.update_data(habit_titles=[text], is_custom=True)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "en"
    await message.answer(
        t("preset.select_weekdays"),
        reply_markup=weekdays_select(t, set(), lang, "day", "back_main"),
    )
