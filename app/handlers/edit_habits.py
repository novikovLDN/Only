"""Edit habits — inline keyboards only."""

from datetime import time as dt_time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import edit_habits_list, edit_habit_detail, main_menu, times_select
from app.utils.i18n import get_weekdays

router = Router(name="edit_habits")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


async def send_edit_habits_screen(msg_or_cb, user, t, session) -> None:
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    if not habits:
        text = t("preset.no_habits")
        kb = main_menu(t)
        if isinstance(msg_or_cb, CallbackQuery):
            await msg_or_cb.message.edit_text(text, reply_markup=kb)
        else:
            await msg_or_cb.answer(text, reply_markup=kb)
        return
    text = t("habit.edit_title")
    habits_tuples = [(h.id, h.title) for h in habits]
    kb = edit_habits_list(t, habits_tuples)
    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.message.edit_text(text, reply_markup=kb)
    else:
        await msg_or_cb.answer(text, reply_markup=kb)


@router.callback_query(F.data == "back_edit")
async def cb_back_edit(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    await cb.answer()
    await state.clear()
    await send_edit_habits_screen(cb, user, t, session)


@router.callback_query(F.data.startswith("editday_"))
async def cb_editday(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    await cb.answer()
    parts = (cb.data or "").split("_")
    if len(parts) < 3:
        return
    habit_id = int(parts[1])
    day_idx = int(parts[2])
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await state.clear()
        await send_edit_habits_screen(cb, user, t, session)
        return
    current_days = {d.weekday for d in habit.days}
    if day_idx in current_days:
        current_days.discard(day_idx)
    else:
        current_days.add(day_idx)
    await habit_repo.update_days(habit, sorted(current_days))
    await session.commit()
    habit = await habit_repo.get_by_id(habit_id)
    lang = user.language or "ru"
    weekdays = get_weekdays(lang)
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    msg = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    current_days = {d.weekday for d in habit.days}
    await cb.message.edit_text(msg, reply_markup=edit_habit_detail(t, habit_id, lang, current_days))


@router.callback_query(F.data.startswith("edit_habit:"))
async def cb_edit_habit(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    await cb.answer()
    habit_id = int((cb.data or "").split(":")[1])
    await state.update_data(editing_habit_id=habit_id)
    await state.set_state("edit:detail")
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await state.clear()
        await send_edit_habits_screen(cb, user, t, session)
        return
    lang = user.language or "ru"
    weekdays = get_weekdays(lang)
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    msg = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    current_days = {d.weekday for d in habit.days}
    await cb.message.edit_text(msg, reply_markup=edit_habit_detail(t, habit_id, lang, current_days))


@router.callback_query(F.data.startswith("del_habit_"))
async def cb_del_habit(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    await cb.answer()
    habit_id = int((cb.data or "").replace("del_habit_", ""))
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        await habit_repo.delete(habit)
        await session.commit()
    await state.clear()
    await send_edit_habits_screen(cb, user, t, session)


@router.callback_query(F.data.startswith("chtime_"))
async def cb_chtime(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    await cb.answer()
    habit_id = int((cb.data or "").replace("chtime_", ""))
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        selected = {t0.time.hour for t0 in habit.times}
        await state.update_data(edit_times=selected)
    await state.set_state("edit:time")
    await state.update_data(editing_habit_id=habit_id)
    data = await state.get_data()
    selected = set(data.get("edit_times", []))
    await cb.message.edit_text(
        t("preset.select_time"),
        reply_markup=times_select(t, selected, f"edittime_{habit_id}", f"edittime_done_{habit_id}", "back_edit"),
    )


@router.callback_query(F.data.startswith("edittime_"))
async def cb_edittime_toggle(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    await cb.answer()
    parts = (cb.data or "").split("_")
    if len(parts) < 3:
        return
    habit_id = int(parts[1])
    h = int(parts[2])
    data = await state.get_data()
    if data.get("editing_habit_id") != habit_id:
        return
    times_set = set(data.get("edit_times", []))
    if h in times_set:
        times_set.discard(h)
    else:
        times_set.add(h)
    await state.update_data(edit_times=list(times_set))
    await cb.message.edit_text(
        t("preset.select_time"),
        reply_markup=times_select(t, times_set, f"edittime_{habit_id}", f"edittime_done_{habit_id}", "back_edit"),
    )


@router.callback_query(F.data.startswith("edittime_done_"))
async def cb_edittime_done(cb: CallbackQuery, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    await cb.answer()
    habit_id = int((cb.data or "").replace("edittime_done_", ""))
    data = await state.get_data()
    if data.get("editing_habit_id") != habit_id:
        await state.clear()
        await send_edit_habits_screen(cb, user, t, session)
        return
    times_list = data.get("edit_times", [])
    if not times_list:
        await cb.message.edit_text(
            t("preset.select_time_at_least") + "\n\n" + t("preset.select_time"),
            reply_markup=times_select(t, set(), f"edittime_{habit_id}", f"edittime_done_{habit_id}", "back_edit"),
        )
        return
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        times_dt = [dt_time(h, 0) for h in sorted(set(times_list))]
        await habit_repo.update_times(habit, times_dt)
        await session.commit()
    await state.set_state("edit:detail")
    habit = await habit_repo.get_by_id(habit_id)
    if habit:
        lang = user.language or "ru"
        weekdays = get_weekdays(lang)
        days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
        times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
        msg = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
        current_days = {d.weekday for d in habit.days}
        await cb.message.edit_text(msg, reply_markup=edit_habit_detail(t, habit_id, lang, current_days))
