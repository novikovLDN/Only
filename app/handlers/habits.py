"""Add habit flow — presets, weekdays, time."""

import logging
from datetime import time as dt_time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.core.constants import HABIT_PRESETS_LIMIT_FREE
from app.i18n.loader import get_presets, get_weekdays

logger = logging.getLogger(__name__)
router = Router(name="habits")


def _presets_keyboard(user, t, is_premium: bool = False) -> InlineKeyboardMarkup:
    presets = get_presets(user.language)
    rows = []
    for i in range(0, min(20, len(presets)), 6):
        row = []
        for j in range(6):
            idx = i + j
            if idx >= len(presets):
                break
            locked = not is_premium and idx >= HABIT_PRESETS_LIMIT_FREE
            label = ("🔒 " if locked else "") + presets[idx]
            cb = f"preset_{idx}" if not locked else "premium"
            row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if row:
            rows.append(row)
    custom_cb = "custom_habit" if is_premium else "premium"
    rows.append([InlineKeyboardButton(text=t("add_custom_habit"), callback_data=custom_cb)])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _weekdays_keyboard(t, selected: list[int]) -> InlineKeyboardMarkup:
    weekdays = get_weekdays("en")
    rows = []
    row = []
    for i, wd in enumerate(weekdays):
        mark = "✅ " if i in selected else ""
        row.append(InlineKeyboardButton(text=f"{mark}{wd}", callback_data=f"day_{i}"))
        if len(row) >= 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("next"), callback_data="days_done")])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _times_keyboard(t, selected: list[int]) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for h in range(24):
        label = f"{h:02d}:00"
        mark = "✅ " if h in selected else ""
        row.append(InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"time_{h}"))
        if len(row) >= 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("done"), callback_data="times_done")])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_presets(message: Message, user, t, is_premium: bool = False) -> None:
    await message.answer(t("select_presets"), reply_markup=_presets_keyboard(user, t, is_premium))


# back_main handled by main_menu router


@router.callback_query(F.data == "premium")
async def premium_locked(callback: CallbackQuery, user, t) -> None:
    from app.keyboards.reply import buy_subscription_kb

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        t("premium_required"),
        reply_markup=buy_subscription_kb(user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("preset_"))
async def preset_selected(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    idx = int(callback.data.split("_")[1])
    presets = get_presets(user.language)
    title = presets[idx]
    await state.update_data(habit_title=title, is_custom=False, selected_days=[], selected_times=[])
    await state.set_state("habit:weekdays")
    await callback.message.edit_text(t("select_weekdays"), reply_markup=_weekdays_keyboard(t, []))
    await callback.answer()


@router.callback_query(F.data.startswith("day_"), F.data != "days_done")
async def day_toggle(callback: CallbackQuery, t, state: FSMContext) -> None:
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    days: list = data.get("selected_days", [])
    if idx in days:
        days.remove(idx)
    else:
        days.append(idx)
    days.sort()
    await state.update_data(selected_days=days)
    await callback.message.edit_reply_markup(reply_markup=_weekdays_keyboard(t, days))
    await callback.answer()


@router.callback_query(F.data == "days_done")
async def days_done(callback: CallbackQuery, user, t, state: FSMContext) -> None:
    data = await state.get_data()
    days = data.get("selected_days", [])
    if not days:
        await callback.answer("Select at least one day", show_alert=True)
        return
    await state.update_data(selected_days=days)
    await state.set_state("habit:times")
    await callback.message.edit_text(t("select_time"), reply_markup=_times_keyboard(t, []))
    await callback.answer()


@router.callback_query(F.data.startswith("time_"), F.data != "times_done")
async def time_toggle(callback: CallbackQuery, t, state: FSMContext) -> None:
    h = int(callback.data.split("_")[1])
    data = await state.get_data()
    times: list = data.get("selected_times", [])
    if h in times:
        times.remove(h)
    else:
        times.append(h)
    times.sort()
    await state.update_data(selected_times=times)
    await callback.message.edit_reply_markup(reply_markup=_times_keyboard(t, times))
    await callback.answer()


@router.callback_query(F.data == "times_done")
async def times_done(callback: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository
    from app.services.habit_service import HabitService
    from app.repositories.user_repo import UserRepository

    data = await state.get_data()
    times = data.get("selected_times", [])
    if not times:
        await callback.answer("Select at least one time", show_alert=True)
        return
    title = data.get("habit_title", "")
    days = data.get("selected_days", [])
    times_dt = [dt_time(h, 0) for h in times]
    habit_repo = HabitRepository(session)
    user_repo = UserRepository(session)
    habit_svc = HabitService(habit_repo, user_repo)
    await habit_svc.create_habit(user, title, False, days, times_dt)
    await session.commit()
    await state.clear()
    from app.keyboards.reply import main_menu_kb
    await callback.message.edit_text(t("habit_saved", title=title))
    await callback.message.answer(t("welcome", username=user.first_name or "User"), reply_markup=main_menu_kb(user.language))
    await callback.answer()
