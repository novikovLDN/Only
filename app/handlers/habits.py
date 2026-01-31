"""
Habit handlers — create, log, callback.
"""

from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.fsm.states import HabitFSM, HabitLogFSM
from app.keyboards.habits import habit_detail_keyboard, habits_list_keyboard
from app.keyboards.main_menu import habit_reminder_keyboard
from app.services.habit_service import HabitService
from app.services.user_service import UserService

router = Router(name="habits")


@router.callback_query(F.data.startswith("habit_done:"))
async def habit_done_cb(callback: CallbackQuery, user, session) -> None:
    """Mark habit as done."""
    habit_id = int(callback.data.split(":")[1])
    svc = HabitService(session)
    log = await svc.log_complete(habit_id, user.id)
    await callback.answer()
    if log:
        await callback.message.answer("✅ Записал! Молодец!")
    else:
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "habit_new")
async def habit_new_cb(callback: CallbackQuery, user, user_service, state: FSMContext) -> None:
    """Start add habit from inline button."""
    await callback.answer()
    can_add, reason = await user_service.can_add_habit(user)
    if not can_add:
        await callback.message.answer(reason)
        return
    await state.set_state(HabitFSM.waiting_name)
    await callback.message.answer("Введи название привычки:")


@router.callback_query(F.data.startswith("habit_select:"))
async def habit_select_cb(callback: CallbackQuery, user, session) -> None:
    """Show habit detail."""
    habit_id = int(callback.data.split(":")[1])
    from app.repositories.habit_repo import HabitRepository

    repo = HabitRepository(session)
    habit = await repo.get_with_schedules(habit_id, user.id)
    await callback.answer()
    if not habit:
        await callback.message.answer("Привычка не найдена.")
        return
    text = f"{habit.emoji or '✅'} <b>{habit.name}</b>\n\n" + (habit.description or "")
    await callback.message.answer(text, reply_markup=habit_detail_keyboard(habit.id))


@router.callback_query(F.data.startswith("habit_skip:"))
async def habit_skip_cb(callback: CallbackQuery, user, session, state: FSMContext) -> None:
    """Mark habit as skipped — ask for optional note."""
    habit_id = int(callback.data.split(":")[1])
    await state.update_data(habit_id=habit_id)
    await state.set_state(HabitLogFSM.adding_decline_note)
    await callback.answer()
    await callback.message.answer("Почему пропускаешь? (напиши причину или /skip)")


@router.message(HabitLogFSM.adding_decline_note, F.text == "/skip")
async def decline_skip_note(message: Message, user, session, state: FSMContext) -> None:
    """Skip without note."""
    data = await state.get_data()
    habit_id = data.get("habit_id")
    await state.clear()
    if habit_id:
        svc = HabitService(session)
        await svc.log_decline(habit_id, user.id)
    await message.answer("Записал пропуск.")


@router.message(HabitLogFSM.adding_decline_note, F.text)
async def decline_with_note(message: Message, user, session, state: FSMContext) -> None:
    """Decline with note."""
    data = await state.get_data()
    habit_id = data.get("habit_id")
    await state.clear()
    if habit_id and message.text:
        svc = HabitService(session)
        await svc.log_decline(habit_id, user.id, note=message.text[:300])
    await message.answer("Записал.")


@router.message(F.text == "➕ Добавить привычку")
async def add_habit_start(message: Message, user, user_service, state: FSMContext) -> None:
    """Start habit creation flow."""
    can_add, reason = await user_service.can_add_habit(user)
    if not can_add:
        await message.answer(reason)
        return
    await state.set_state(HabitFSM.waiting_name)
    await message.answer("Введи название привычки:")


@router.message(HabitFSM.waiting_name, F.text)
async def habit_name_entered(message: Message, state: FSMContext) -> None:
    """Save habit name, ask for description."""
    from app.utils.validators import validate_habit_name

    name = validate_habit_name(message.text)
    if not name:
        await message.answer("Некорректное название. Попробуй ещё раз.")
        return
    await state.update_data(name=name)
    await state.set_state(HabitFSM.waiting_schedule_time)
    await message.answer(f"Отлично! Во сколько напоминать? (например 09:00)")


@router.message(HabitFSM.waiting_schedule_time, F.text)
async def habit_time_entered(message: Message, user, session, state: FSMContext) -> None:
    """Save time and create habit."""
    from app.utils.validators import validate_time

    time_str = validate_time(message.text)
    if not time_str:
        await message.answer("Введи время в формате ЧЧ:ММ (например 09:00)")
        return
    data = await state.get_data()
    name = data.get("name", "Привычка")
    await state.clear()
    svc = HabitService(session)
    habit = await svc.create_habit(user.id, name=name, reminder_time=time_str)
    if habit:
        await message.answer(f"✅ Привычка «{name}» создана! Напоминание в {time_str}.")
    else:
        await message.answer("Не удалось создать привычку.")
