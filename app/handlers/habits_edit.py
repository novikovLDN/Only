"""Edit habits — grid, change days/time, delete."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.keyboards.habits import edit_habit_menu, habits_list, weekdays_keyboard, time_keyboard
from app.services import habit_service, user_service
from app.texts import t

router = Router(name="habits_edit")


@router.callback_query(lambda c: c.data == "edit_habits")
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
        await cb.message.edit_text(t(lang, "btn_edit_habits") + "\n\nНет привычек.", reply_markup=back_only(lang))
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
        f"{habit.title}\n\nИзменить дни / время / удалить:",
        reply_markup=edit_habit_menu(habit_id, lang),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("habit_delete:"))
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

    await cb.message.edit_text(t(lang, "habit_created"), reply_markup=main_menu(lang))
