"""Edit habits."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.i18n import get_weekdays
from app.keyboards.inline import main_menu, back_only, edit_habit_detail, weekdays_select, times_select

router = Router(name="edit_habits")


async def build_edit_habits_screen(user, t, session) -> tuple[str, InlineKeyboardMarkup]:
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    lang = user.language or "en"
    if not habits:
        return t("preset.no_habits"), main_menu(t)
    rows = []
    for h in habits:
        rows.append([InlineKeyboardButton(text=h.title, callback_data=f"edit_habit_{h.id}")])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")])
    return t("habit.edit_title"), InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("edit_habit_"))
async def edit_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    lang = user.language or "en"
    weekdays = get_weekdays(lang)
    days_set = {d.weekday for d in habit.days}
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    text = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    await callback.message.edit_text(text, reply_markup=edit_habit_detail(t, habit_id, lang, days_set))
    await callback.answer()


@router.callback_query(F.data == "back_edit")
async def back_edit(callback: CallbackQuery, user, t, session) -> None:
    text, kb = await build_edit_habits_screen(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


def _edit_habit_back_cb(habit_id: int) -> str:
    return f"et_back_{habit_id}"


@router.callback_query(F.data.startswith("chtime_"))
async def change_time_start(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[1])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    selected_times = {t0.time.hour for t0 in habit.times}
    await callback.message.edit_text(
        t("preset.select_time"),
        reply_markup=times_select(t, selected_times, f"et_{habit_id}", f"et_done_{habit_id}", _edit_habit_back_cb(habit_id)),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^et_\d+_\d+$"))
async def edit_time_toggle(callback: CallbackQuery, user, t, session) -> None:
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer()
        return
    habit_id = int(parts[1])
    h = int(parts[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    times_set = {t0.time.hour for t0 in habit.times}
    if h in times_set:
        times_set.discard(h)
    else:
        times_set.add(h)
    from datetime import time as dt_time

    habit = await habit_repo.get_by_id(habit_id)
    await habit_repo.update_times(habit, [dt_time(hh, 0) for hh in sorted(times_set)])
    await session.commit()
    await callback.message.edit_reply_markup(
        reply_markup=times_select(t, times_set, f"et_{habit_id}", f"et_done_{habit_id}", _edit_habit_back_cb(habit_id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("et_back_"))
async def edit_time_back(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    lang = user.language or "en"
    weekdays = get_weekdays(lang)
    days_set = {d.weekday for d in habit.days}
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    text = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    await callback.message.edit_text(text, reply_markup=edit_habit_detail(t, habit_id, lang, days_set))
    await callback.answer()


@router.callback_query(F.data.startswith("et_done_"))
async def edit_time_done(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    lang = user.language or "en"
    weekdays = get_weekdays(lang)
    days_set = {d.weekday for d in habit.days}
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    text = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    await callback.message.edit_text(text, reply_markup=edit_habit_detail(t, habit_id, lang, days_set))
    await callback.answer()


@router.callback_query(F.data.startswith("editday_"))
async def edit_day_toggle(callback: CallbackQuery, user, t, session) -> None:
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer()
        return
    habit_id = int(parts[1])
    day_idx = int(parts[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    days_set = {d.weekday for d in habit.days}
    if day_idx in days_set:
        days_set.discard(day_idx)
    else:
        days_set.add(day_idx)
    await habit_repo.update_days(habit, list(days_set))
    await session.commit()
    habit = await habit_repo.get_by_id(habit_id)
    lang = user.language or "en"
    weekdays = get_weekdays(lang)
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    text = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
    await callback.message.edit_text(text, reply_markup=edit_habit_detail(t, habit_id, lang, days_set))
    await callback.answer()


@router.callback_query(F.data.startswith("del_habit_"))
async def delete_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        await habit_repo.delete(habit)
        await session.commit()
    text, kb = await build_edit_habits_screen(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
