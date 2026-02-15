"""Edit habits — Reply keyboard only."""

from datetime import time as dt_time

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.reply import edit_habits_list, edit_habit_detail, main_menu, times_select
from app.utils.i18n import get_weekdays

router = Router(name="edit_habits")

BTN_BACK = ("🔙 Back", "🔙 Назад")
TIME_EMOJI = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"] * 2


async def send_edit_habits_screen(message: Message, user, t, session) -> None:
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    if not habits:
        await message.answer(
            t("preset.no_habits"),
            reply_markup=main_menu(t),
        )
        return
    text = t("habit.edit_title")
    titles = [h.title for h in habits]
    await message.answer(text, reply_markup=edit_habits_list(t, titles))


@router.message(F.text)
async def edit_habit_nav(message: Message, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    text = message.text or ""
    if text in BTN_BACK:
        data = await state.get_data()
        await state.clear()
        if "editing_habit_id" in data:
            await send_edit_habits_screen(message, user, t, session)
        else:
            name = user.first_name or "User"
            text_msg = t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
            await message.answer(text_msg, reply_markup=main_menu(t))
        return

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    habit_titles = {h.title: h for h in habits}

    if text in habit_titles:
        habit = habit_titles[text]
        await state.update_data(editing_habit_id=habit.id)
        await state.set_state("edit:detail")
        lang = user.language or "ru"
        weekdays = get_weekdays(lang)
        days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
        times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
        msg = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
        await message.answer(msg, reply_markup=edit_habit_detail(t))
        return

    data = await state.get_data()
    habit_id = data.get("editing_habit_id")
    if not habit_id:
        return

    if text == t("habit.change_time"):
        habit = await habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user.id:
            selected = [t0.time.hour for t0 in habit.times]
            await state.update_data(edit_times=selected)
        await state.set_state("edit:time")
        from app.keyboards.reply import times_select
        await message.answer(t("preset.select_time"), reply_markup=times_select(t))
        return

    if text == t("habit.delete"):
        habit = await habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user.id:
            await habit_repo.delete(habit)
            await session.commit()
        await state.clear()
        await send_edit_habits_screen(message, user, t, session)
        return


@router.message(StateFilter("edit:time"), F.text)
async def edit_time_nav(message: Message, user, t, session, state: FSMContext) -> None:
    from app.repositories.habit_repo import HabitRepository

    text = message.text or ""
    data = await state.get_data()
    habit_id = data.get("editing_habit_id")
    if not habit_id:
        await state.clear()
        await send_edit_habits_screen(message, user, t, session)
        return

    if text == t("btn.back"):
        await state.set_state("edit:detail")
        habit_repo = HabitRepository(session)
        habit = await habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user.id:
            lang = user.language or "ru"
            weekdays = get_weekdays(lang)
            days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
            times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
            msg = f"{habit.title}\n{t('habit.days_label')}: {days_str}\n{t('habit.times_label')}: {times_str}"
            await message.answer(msg, reply_markup=edit_habit_detail(t))
        return

    if text == t("btn.done"):
        times_list = data.get("edit_times", [])
        if not times_list:
            await message.answer(t("preset.select_time_at_least"), reply_markup=times_select(t))
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
            await message.answer(msg, reply_markup=edit_habit_detail(t))
        return

    for h in range(24):
        label = f"{TIME_EMOJI[h]} {h:02d}:00"
        if text == label:
            times_set = set(data.get("edit_times", []))
            if h in times_set:
                times_set.discard(h)
            else:
                times_set.add(h)
            await state.update_data(edit_times=list(times_set))
            await message.answer(t("preset.select_time"), reply_markup=times_select(t))
            return
