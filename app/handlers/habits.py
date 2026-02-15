"""Add habit flow — Reply keyboard only."""

import logging
from datetime import time as dt_time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.utils.i18n import get_presets, get_weekdays
from app.keyboards.reply import (
    presets_page,
    weekdays_select,
    times_select,
    main_menu,
    buy_subscription_only,
)
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
    message: Message, user, t, is_premium: bool, page: int = 0,
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
    await message.answer(
        _habit_text(t) + extra,
        reply_markup=presets_page(t, lang, page, is_premium),
    )


@router.message(AddHabitStates.presets, F.text)
async def preset_button(message: Message, user, t, is_premium: bool, state: FSMContext) -> None:
    lang = user.language or "ru"
    presets = get_presets(lang)
    text = (message.text or "").strip()

    if text == t("btn.add_custom"):
        await state.update_data(habit_titles=[], is_custom=True)
        await state.set_state(AddHabitStates.custom_text)
        await message.answer(t("preset.enter_custom"), reply_markup=main_menu(t))
        return

    if text == t("preset.nav_back"):
        data = await state.get_data()
        page = data.get("current_page", 0)
        if page == 0:
            await state.clear()
            await message.answer(_welcome(user, t), reply_markup=main_menu(t))
        else:
            await send_presets_screen(message, user, t, is_premium, page - 1, set(data.get("selected_habits", [])), state)
        return

    if text == t("preset.nav_next"):
        data = await state.get_data()
        selected = set(data.get("selected_habits", []))
        if not selected:
            await message.answer(t("preset.select_at_least_one"), reply_markup=presets_page(t, lang, data.get("current_page", 0), is_premium))
            return
        titles = [presets[i] for i in sorted(selected)]
        await state.update_data(habit_titles=titles, is_custom=False)
        await state.set_state(AddHabitStates.weekdays)
        await message.answer(
            t("preset.select_weekdays"),
            reply_markup=weekdays_select(t, lang),
        )
        return

    idx = next((i for i, p in enumerate(presets) if p == text or f"🔒 {p}" == text), None)
    if idx is not None:
        if not is_premium and idx >= HABIT_PRESETS_LIMIT_FREE:
            await message.answer(t("premium.block"), reply_markup=buy_subscription_only(t))
            return
        data = await state.get_data()
        selected = set(data.get("selected_habits", []))
        page = data.get("current_page", 0)
        if idx in selected:
            selected.discard(idx)
        else:
            selected.add(idx)
        await send_presets_screen(message, user, t, is_premium, page, selected, state)
        return


@router.message(AddHabitStates.custom_text, F.text)
async def custom_habit_text(message: Message, user, t, state: FSMContext) -> None:
    text = (message.text or "").strip()
    menu_buttons = [t("btn.add_habit"), t("btn.edit_habits"), t("btn.loyalty"), t("btn.subscribe"), t("btn.settings"), t("btn.support"), t("btn.back")]
    if text in menu_buttons:
        return
    if len(text) < 1 or len(text) > 100:
        await message.answer(t("preset.custom_invalid"), reply_markup=main_menu(t))
        return
    await state.update_data(habit_titles=[text], is_custom=True)
    await state.set_state(AddHabitStates.weekdays)
    lang = user.language or "ru"
    await message.answer(
        t("preset.select_weekdays"),
        reply_markup=weekdays_select(t, lang),
    )


@router.message(AddHabitStates.weekdays, F.text)
async def weekday_button(message: Message, user, t, is_premium: bool, state: FSMContext) -> None:
    lang = user.language or "ru"
    weekdays = get_weekdays(lang)
    text = message.text or ""

    if text == t("btn.done"):
        data = await state.get_data()
        days = data.get("selected_days", [])
        if not days:
            await message.answer(t("preset.select_day"), reply_markup=weekdays_select(t, lang))
            return
        days_sorted = sorted(set(days))
        await state.update_data(selected_days=days_sorted)
        await state.set_state(AddHabitStates.times)
        await message.answer(t("preset.select_time"), reply_markup=times_select(t))
        return

    if text == t("btn.back"):
        await state.set_state(AddHabitStates.presets)
        data = await state.get_data()
        await send_presets_screen(message, user, t, is_premium, data.get("current_page", 0), set(data.get("selected_habits", [])), state)
        return

    idx = next((i for i, w in enumerate(weekdays) if w == text), None)
    if idx is not None:
        data = await state.get_data()
        days = set(data.get("selected_days", []))
        if idx in days:
            days.discard(idx)
        else:
            days.add(idx)
        await state.update_data(selected_days=list(days))
        sel_str = ", ".join(weekdays[i] for i in sorted(days)) if days else ""
        extra = f"\n\n✅ {sel_str}" if sel_str else ""
        await message.answer(
            t("preset.select_weekdays") + extra,
            reply_markup=weekdays_select(t, lang),
        )


@router.message(AddHabitStates.times, F.text)
async def time_button(message: Message, user, t, session, state: FSMContext) -> None:
    text = message.text or ""

    if text == t("btn.done"):
        data = await state.get_data()
        times_list = data.get("selected_times", [])
        if not times_list:
            await message.answer(t("preset.select_time_at_least"), reply_markup=times_select(t))
            return
        titles = data.get("habit_titles", [])
        if not titles:
            await state.clear()
            await message.answer(_welcome(user, t), reply_markup=main_menu(t))
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
        await message.answer(_welcome(user, t), reply_markup=main_menu(t))
        return

    if text == t("btn.back"):
        await state.set_state(AddHabitStates.weekdays)
        data = await state.get_data()
        lang = user.language or "ru"
        await message.answer(
            t("preset.select_weekdays"),
            reply_markup=weekdays_select(t, lang),
        )
        return

    TIME_EMOJI = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"] * 2
    for h in range(24):
        label = f"{TIME_EMOJI[h]} {h:02d}:00"
        if text == label:
            data = await state.get_data()
            times_set = set(data.get("selected_times", []))
            if h in times_set:
                times_set.discard(h)
            else:
                times_set.add(h)
            await state.update_data(selected_times=list(times_set))
            await message.answer(t("preset.select_time"), reply_markup=times_select(t))
            return
