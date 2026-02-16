"""Edit habits — grid, change days/time, delete."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.keyboards.habits import (
    edit_habit_menu,
    edit_time_keyboard_for_habit,
    edit_weekdays_keyboard,
    habits_list,
)
from app.services import achievement_service, habit_service, metrics_service, user_service
from app.texts import t

router = Router(name="habits_edit")


@router.callback_query(F.data == "edit_habits")
async def cb_edit_habits(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        habits = await habit_service.get_user_habits(session, user.id)

    if not habits:
        await cb.message.edit_text(t(lang, "btn_edit_habits") + "\n\n" + t(lang, "edit_no_habits"), reply_markup=back_only(lang))
        return

    hs = [(h.id, h.title) for h in habits]
    await cb.message.edit_text(t(lang, "btn_edit_habits"), reply_markup=habits_list(hs, lang))


@router.callback_query(lambda c: c.data and c.data.startswith("habit_") and ":" not in (c.data or ""))
async def cb_habit_detail(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split("_")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code

    await cb.message.edit_text(
        f"{habit.title}\n\n{t(lang, 'edit_habit_prompt')}",
        reply_markup=edit_habit_menu(habit_id, lang),
    )


@router.callback_query(F.data.startswith("edit_days:"))
async def cb_edit_days(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code
        times_data = await habit_service.get_habit_times(session, habit_id)
        active_days = sorted({w for w, _ in times_data})

    await cb.message.edit_text(
        t(lang, "habit_select_days"),
        reply_markup=edit_weekdays_keyboard(habit_id, active_days, lang),
    )


@router.callback_query(F.data.startswith("edit_wd:"))
async def cb_edit_wd_toggle(cb: CallbackQuery) -> None:
    await cb.answer()
    parts = cb.data.split(":")
    habit_id = int(parts[1])
    day = int(parts[2])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code
        times_data = await habit_service.get_habit_times(session, habit_id)
        active_days = sorted({w for w, _ in times_data})
        active_times = [t for _, t in times_data]

        goal_increased = False
        if day in active_days:
            active_days = [d for d in active_days if d != day]
        else:
            active_days = sorted(active_days + [day])
            goal_increased = True

        if active_days and active_times:
            await habit_service.update_habit_times(session, habit_id, active_days, active_times)
            await metrics_service.mark_habit_modified(session, user.id, user)
            if goal_increased:
                await metrics_service.mark_habit_goal_increased(session, user.id)
            await session.commit()
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="habit_modified"
            )
            await session.commit()

    await cb.message.edit_text(
        t(lang, "habit_select_days"),
        reply_markup=edit_weekdays_keyboard(habit_id, active_days, lang),
    )


@router.callback_query(F.data.startswith("edit_days_ok:"))
async def cb_edit_days_ok(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code

    await cb.message.edit_text(
        f"{habit.title}\n\n{t(lang, 'edit_habit_prompt')}",
        reply_markup=edit_habit_menu(habit_id, lang),
    )


@router.callback_query(F.data.startswith("edit_time:"))
async def cb_edit_time(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code
        times_data = await habit_service.get_habit_times(session, habit_id)
        active_times = sorted({t for _, t in times_data})

    await cb.message.edit_text(
        t(lang, "habit_select_time"),
        reply_markup=edit_time_keyboard_for_habit(habit_id, active_times, lang),
    )


@router.callback_query(F.data.startswith("edit_tm:"))
async def cb_edit_tm_toggle(cb: CallbackQuery) -> None:
    await cb.answer()
    parts = cb.data.split(":")
    habit_id = int(parts[1])
    t_slot = parts[2]
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code
        times_data = await habit_service.get_habit_times(session, habit_id)
        active_days = sorted({w for w, _ in times_data})
        active_times = list({t for _, t in times_data})

        goal_increased = False
        if t_slot in active_times:
            active_times = [x for x in active_times if x != t_slot]
        else:
            active_times = active_times + [t_slot]
            goal_increased = True
        active_times = sorted(active_times)

        if active_days and active_times:
            await habit_service.update_habit_times(session, habit_id, active_days, active_times)
            await metrics_service.mark_habit_modified(session, user.id, user)
            if goal_increased:
                await metrics_service.mark_habit_goal_increased(session, user.id)
            await session.commit()
            await achievement_service.check_achievements(
                session, user.id, user, cb.bot, user.telegram_id, trigger="habit_modified"
            )
            await session.commit()

    await cb.message.edit_text(
        t(lang, "habit_select_time"),
        reply_markup=edit_time_keyboard_for_habit(habit_id, active_times, lang),
    )


@router.callback_query(F.data.startswith("edit_time_ok:"))
async def cb_edit_time_ok(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        lang = user.language_code

    await cb.message.edit_text(
        f"{habit.title}\n\n{t(lang, 'edit_habit_prompt')}",
        reply_markup=edit_habit_menu(habit_id, lang),
    )


@router.callback_query(F.data.startswith("habit_delete:"))
async def cb_habit_delete(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        habit = await habit_service.get_by_id(session, habit_id)
        if not habit or habit.user_id != user.id:
            return
        await habit_service.delete_habit(session, habit)
        await session.commit()
        lang = user.language_code

    await cb.message.edit_text(
        t(lang, "habit_deleted"),
        reply_markup=main_menu(lang, user_service.is_premium(user)),
    )
