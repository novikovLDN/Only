"""
Habit handlers — create, log, callback.

FSM управляет flow, domain services — бизнес-логика.
"""

from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.fsm.context_data import (
    FSM_DECLINE_HABIT_ID,
    FSM_HABIT_DAYS,
    FSM_HABIT_EMOJI,
    FSM_HABIT_NAME,
    FSM_HABIT_TEMPLATE_ID,
    FSM_HABIT_TIMES,
)
from app.fsm.constants import HABIT_TEMPLATES, TIME_SLOTS
from app.fsm.states import HabitCreateFSM, HabitDeclineFSM
from app.keyboards.fsm_habits import (
    habit_confirm_keyboard,
    habit_days_keyboard,
    habit_decline_presets_keyboard,
    habit_template_keyboard,
    habit_time_keyboard,
)
from app.keyboards.habits import habit_detail_keyboard, habits_list_keyboard
from app.keyboards.main_menu import habit_reminder_keyboard
from app.services.habit_service import HabitService
from app.utils.keyboard import edit_reply_markup_if_changed
from app.utils.message_lifecycle import send_screen_from_event
from app.services.user_service import UserService
from app.texts import (
    HABIT_CONFIRM_PROMPT,
    HABIT_CREATE_FAILED,
    HABIT_CREATE_START,
    HABIT_CREATED,
    HABIT_DAYS_PROMPT,
    HABIT_DAYS_REQUIRED,
    HABIT_DECLINE_WHY,
    HABIT_DECLINE_RECORDED,
    HABIT_DONE_ERROR,
    HABIT_DONE_SUCCESS,
    HABIT_NAME_INVALID,
    HABIT_NAME_PROMPT,
    HABIT_NOT_FOUND,
    HABIT_TIME_PROMPT,
    HABIT_TIME_REQUIRED,
    HABIT_CANCELLED,
)

router = Router(name="habits")


# --- Log (done/decline) — без FSM или HabitDeclineFSM ---

@router.callback_query(F.data.startswith("habit_done:"))
async def habit_done_cb(callback: CallbackQuery, user, session) -> None:
    """Mark habit as done. Check achievements, show reward if new."""
    await callback.answer()
    habit_id = int(callback.data.split(":")[1])
    svc = HabitService(session)
    log = await svc.log_complete(habit_id, user.id)
    if not log:
        await callback.answer(HABIT_DONE_ERROR, show_alert=True)
        return
    from app.services.achievement_service import AchievementService
    from app.utils.message_lifecycle import send_screen_from_event

    ach_svc = AchievementService(session)
    new_ach = await ach_svc.check_and_unlock(user)
    if new_ach:
        from app.keyboards.profile import achievement_reward_keyboard
        from app.texts import ACHIEVEMENT_NEW_TITLE, ACHIEVEMENT_REWARD
        reward_text = f"{ACHIEVEMENT_NEW_TITLE}\n\n{ACHIEVEMENT_REWARD.format(icon=new_ach.icon, title=new_ach.title, description=new_ach.description)}"
        await send_screen_from_event(
            callback, user.id, reward_text,
            reply_markup=achievement_reward_keyboard(),
        )
    else:
        await callback.message.answer(HABIT_DONE_SUCCESS)


@router.callback_query(F.data.startswith("habit_skip:"))
async def habit_skip_cb(callback: CallbackQuery, user, session, state: FSMContext) -> None:
    """Mark habit as skipped — переход в FSM для комментария."""
    await callback.answer()
    habit_id = int(callback.data.split(":")[1])
    await state.update_data(**{FSM_DECLINE_HABIT_ID: habit_id})
    await state.set_state(HabitDeclineFSM.adding_note)
    await callback.message.answer(
        HABIT_DECLINE_WHY,
        reply_markup=habit_decline_presets_keyboard(),
    )


@router.callback_query(F.data.startswith("habit_decline_preset:"))
async def habit_decline_preset_cb(callback: CallbackQuery, user, session, state: FSMContext) -> None:
    """Decline с preset или skip. Streak lost message for free users."""
    await callback.answer()
    preset = callback.data.split(":")[1]
    data = await state.get_data()
    habit_id = data.get(FSM_DECLINE_HABIT_ID)
    await state.clear()
    if habit_id:
        from app.config.constants import UserTier
        from app.repositories.habit_repo import HabitRepository

        repo = HabitRepository(session)
        streak_before = await repo.get_current_streak(user.id)
        svc = HabitService(session)
        if preset == "skip":
            await svc.log_decline(habit_id, user.id)
        else:
            await svc.log_decline(habit_id, user.id, preset=preset)
        if streak_before >= 1 and user.tier != UserTier.PREMIUM:
            from app.keyboards.profile import streak_lost_keyboard
            from app.texts import STREAK_LOST_FREE
            from app.utils.message_lifecycle import send_screen_from_event
            await send_screen_from_event(
                callback, user.id, STREAK_LOST_FREE,
                reply_markup=streak_lost_keyboard(),
            )
            return
    await callback.message.answer(HABIT_DECLINE_RECORDED)


@router.message(HabitDeclineFSM.adding_note, F.text == "/skip")
async def habit_decline_skip(message: Message, user, session, state: FSMContext) -> None:
    """Пропуск без комментария. Streak lost for free users."""
    data = await state.get_data()
    habit_id = data.get(FSM_DECLINE_HABIT_ID)
    await state.clear()
    if habit_id:
        from app.config.constants import UserTier
        from app.repositories.habit_repo import HabitRepository

        repo = HabitRepository(session)
        streak_before = await repo.get_current_streak(user.id)
        svc = HabitService(session)
        await svc.log_decline(habit_id, user.id)
        if streak_before >= 1 and user.tier != UserTier.PREMIUM:
            from app.keyboards.profile import streak_lost_keyboard
            from app.texts import STREAK_LOST_FREE
            from app.utils.message_lifecycle import send_screen_from_event
            await send_screen_from_event(
                message, user.id, STREAK_LOST_FREE,
                reply_markup=streak_lost_keyboard(),
            )
            return
    await message.answer(HABIT_DECLINE_RECORDED)


@router.message(HabitDeclineFSM.adding_note, F.text)
async def habit_decline_with_text(message: Message, user, session, state: FSMContext) -> None:
    """Decline с произвольным текстом. Streak lost for free users."""
    data = await state.get_data()
    habit_id = data.get(FSM_DECLINE_HABIT_ID)
    await state.clear()
    if habit_id and message.text:
        from app.config.constants import UserTier
        from app.repositories.habit_repo import HabitRepository

        repo = HabitRepository(session)
        streak_before = await repo.get_current_streak(user.id)
        svc = HabitService(session)
        await svc.log_decline(habit_id, user.id, note=message.text[:300])
        if streak_before >= 1 and user.tier != UserTier.PREMIUM:
            from app.keyboards.profile import streak_lost_keyboard
            from app.texts import STREAK_LOST_FREE
            from app.utils.message_lifecycle import send_screen_from_event
            await send_screen_from_event(
                message, user.id, STREAK_LOST_FREE,
                reply_markup=streak_lost_keyboard(),
            )
            return
    await message.answer(HABIT_DECLINE_RECORDED)


@router.callback_query(F.data.startswith("habit_select:"))
async def habit_select_cb(callback: CallbackQuery, user, session) -> None:
    """Show habit detail."""
    await callback.answer()
    habit_id = int(callback.data.split(":")[1])
    from app.fsm.constants import WEEKDAYS
    from app.repositories.habit_repo import HabitRepository

    repo = HabitRepository(session)
    habit = await repo.get_with_schedules(habit_id, user.id)
    if not habit:
        await send_screen_from_event(callback, user.id, HABIT_NOT_FOUND)
        return
    lines = [f"{habit.emoji or '✅'} <b>{habit.name}</b>"]
    if habit.description:
        lines.append(habit.description)
    if habit.schedules:
        days_set = set()
        times_list = []
        for s in habit.schedules:
            if s.days_of_week:
                days_set.update(int(d) for d in s.days_of_week.split(",") if d.strip())
            times_list.append(s.reminder_time)
        if days_set:
            days_str = ", ".join(WEEKDAYS[d] for d in sorted(days_set) if 0 <= d <= 6)
            lines.append(f"Дни: {days_str}")
        if times_list:
            times_str = ", ".join(sorted(set(times_list)))
            lines.append(f"Время: {times_str}")
    text = "\n\n".join(lines)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=habit_detail_keyboard(habit.id),
    )


# --- Habit Create FSM ---

@router.message(F.text == "➕ Добавить привычку")
async def add_habit_start_msg(message: Message, user, user_service, state: FSMContext) -> None:
    """Старт создания привычки (из меню)."""
    can_add, reason = await user_service.can_add_habit(user)
    if not can_add:
        await message.answer(reason)
        return
    await state.clear()
    await state.set_state(HabitCreateFSM.choosing_template)
    await message.answer(HABIT_CREATE_START, reply_markup=habit_template_keyboard())


@router.callback_query(F.data == "habit_new")
async def add_habit_start_cb(callback: CallbackQuery, user, user_service, state: FSMContext) -> None:
    """Старт создания привычки (из списка привычек)."""
    await callback.answer()
    can_add, reason = await user_service.can_add_habit(user)
    if not can_add:
        await callback.message.answer(reason)
        return
    await state.clear()
    await state.set_state(HabitCreateFSM.choosing_template)
    await callback.message.answer(HABIT_CREATE_START, reply_markup=habit_template_keyboard())


@router.callback_query(F.data.startswith("habit_tpl:"), HabitCreateFSM.choosing_template)
async def habit_template_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Шаблон выбран — template или custom."""
    await callback.answer()
    tpl = callback.data.split(":")[1]
    if tpl == "custom":
        await state.set_state(HabitCreateFSM.waiting_name)
        await callback.message.answer(HABIT_NAME_PROMPT)
        return
    if tpl in HABIT_TEMPLATES:
        name, emoji = HABIT_TEMPLATES[tpl]
        await state.update_data(**{
            FSM_HABIT_TEMPLATE_ID: tpl,
            FSM_HABIT_NAME: name,
            FSM_HABIT_EMOJI: emoji,
        })
        await state.set_state(HabitCreateFSM.choosing_days)
        await callback.message.answer(HABIT_DAYS_PROMPT, reply_markup=habit_days_keyboard([]))


@router.message(HabitCreateFSM.waiting_name, F.text)
async def habit_name_entered(message: Message, state: FSMContext) -> None:
    """Название введено (своя привычка)."""
    from app.utils.validators import validate_habit_name

    name = validate_habit_name(message.text)
    if not name:
        await message.answer(HABIT_NAME_INVALID)
        return
    await state.update_data(**{FSM_HABIT_NAME: name, FSM_HABIT_EMOJI: None})
    await state.set_state(HabitCreateFSM.choosing_days)
    await message.answer(HABIT_DAYS_PROMPT, reply_markup=habit_days_keyboard([]))


@router.callback_query(F.data.startswith("habit_day:"), HabitCreateFSM.choosing_days)
async def habit_day_toggle_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Toggle дня в multi-select."""
    await callback.answer()
    day = int(callback.data.split(":")[1])
    data = await state.get_data()
    days: list[int] = list(data.get(FSM_HABIT_DAYS) or [])
    if day in days:
        days.remove(day)
    else:
        days.append(day)
    await state.update_data(**{FSM_HABIT_DAYS: days})
    await edit_reply_markup_if_changed(callback.message, habit_days_keyboard(days))


@router.callback_query(F.data == "habit_days_ok", HabitCreateFSM.choosing_days)
async def habit_days_confirm_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение дней → выбор времени."""
    data = await state.get_data()
    days = data.get(FSM_HABIT_DAYS) or []
    if not days:
        await callback.answer(HABIT_DAYS_REQUIRED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(HabitCreateFSM.choosing_time)
    await callback.message.answer(HABIT_TIME_PROMPT, reply_markup=habit_time_keyboard([]))


@router.callback_query(F.data.startswith("habit_time:"), HabitCreateFSM.choosing_time)
async def habit_time_toggle_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Toggle времени в multi-select."""
    await callback.answer()
    time_slot = callback.data.split(":", 1)[1]  # "habit_time:06:00" -> "06:00"
    data = await state.get_data()
    times: list[str] = list(data.get(FSM_HABIT_TIMES) or [])
    if time_slot in times:
        times.remove(time_slot)
    else:
        times.append(time_slot)
    await state.update_data(**{FSM_HABIT_TIMES: times})
    await edit_reply_markup_if_changed(callback.message, habit_time_keyboard(times))


@router.callback_query(F.data == "habit_time_ok", HabitCreateFSM.choosing_time)
async def habit_time_confirm_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение времени → подтверждение создания."""
    data = await state.get_data()
    times = data.get(FSM_HABIT_TIMES) or []
    if not times:
        await callback.answer(HABIT_TIME_REQUIRED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(HabitCreateFSM.confirming)
    name = data.get(FSM_HABIT_NAME, "Привычка")
    days = data.get(FSM_HABIT_DAYS) or []
    days_str = ", ".join(["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][d] for d in sorted(days))
    times_str = ", ".join(sorted(times))
    text = HABIT_CONFIRM_PROMPT.format(name=name, days=days_str, times=times_str)
    await callback.message.answer(text, reply_markup=habit_confirm_keyboard())


@router.callback_query(F.data.startswith("habit_confirm:"), HabitCreateFSM.confirming)
async def habit_confirm_cb(callback: CallbackQuery, user, session, state: FSMContext) -> None:
    """Финальное подтверждение — вызов domain service или возврат к редактированию."""
    await callback.answer()
    if callback.data.endswith(":edit"):
        await state.set_state(HabitCreateFSM.choosing_time)
        data = await state.get_data()
        times = data.get(FSM_HABIT_TIMES) or []
        await callback.message.answer(
            HABIT_TIME_PROMPT,
            reply_markup=habit_time_keyboard(times),
        )
        return
    if callback.data.endswith(":no"):
        await state.clear()
        await callback.message.answer(HABIT_CANCELLED)
        return
    data = await state.get_data()
    name = data.get(FSM_HABIT_NAME, "Привычка")
    days = data.get(FSM_HABIT_DAYS) or [0, 1, 2, 3, 4]
    times = data.get(FSM_HABIT_TIMES) or ["09:00"]
    emoji = data.get(FSM_HABIT_EMOJI)
    await state.clear()
    svc = HabitService(session)
    days_str = ",".join(str(d) for d in sorted(days))
    habit = await svc.create_habit(
        user.id,
        name=name,
        emoji=emoji,
        reminder_times=sorted(times),
        days_of_week=days_str,
    )
    if habit:
        from app.services.achievement_service import AchievementService
        from app.utils.message_lifecycle import send_screen_from_event

        ach_svc = AchievementService(session)
        new_ach = await ach_svc.check_and_unlock(user)
        if new_ach:
            from app.keyboards.profile import achievement_reward_keyboard
            from app.texts import ACHIEVEMENT_NEW_TITLE, ACHIEVEMENT_REWARD
            reward_text = f"{ACHIEVEMENT_NEW_TITLE}\n\n{ACHIEVEMENT_REWARD.format(icon=new_ach.icon, title=new_ach.title, description=new_ach.description)}"
            await send_screen_from_event(
                callback, user.id, reward_text,
                reply_markup=achievement_reward_keyboard(),
            )
        else:
            await callback.message.answer(HABIT_CREATED.format(name=name))
    else:
        await callback.message.answer(HABIT_CREATE_FAILED)
