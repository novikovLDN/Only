"""Habits — add, list."""

from datetime import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.services import habits as habit_svc
from app.texts import t

router = Router(name="habits")


class AddHabitStates(StatesGroup):
    name = State()
    time = State()


@router.callback_query(lambda c: c.data == "add_habit")
async def cb_add_habit(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code
    await state.set_state(AddHabitStates.name)
    await cb.message.edit_text(t(lang, "habit_name_prompt"), reply_markup=back_only(lang))


@router.message(AddHabitStates.name, F.text)
async def habit_name_entered(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 1 or len(text) > 100:
        tid = message.from_user.id if message.from_user else 0
        sm = get_session_maker()
        async with sm() as session:
            from sqlalchemy import select
            from app.models import User
            r = await session.execute(select(User).where(User.telegram_id == tid))
            user = r.scalar_one_or_none()
            lang = user.language_code if user else "en"
        await message.answer(t(lang, "habit_name_prompt"), reply_markup=back_only(lang))
        return
    await state.update_data(habit_title=text)
    await state.set_state(AddHabitStates.time)
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        lang = user.language_code if user else "en"
    await message.answer(t(lang, "habit_time_prompt"), reply_markup=back_only(lang))


@router.message(AddHabitStates.time, F.text)
async def habit_time_entered(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        parts = text.split(":")
        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        remind_time = time(h % 24, m % 60)
    except (ValueError, IndexError):
        tid = message.from_user.id if message.from_user else 0
        sm = get_session_maker()
        async with sm() as session:
            from sqlalchemy import select
            from app.models import User
            r = await session.execute(select(User).where(User.telegram_id == tid))
            user = r.scalar_one_or_none()
            lang = user.language_code if user else "en"
        await message.answer(t(lang, "habit_time_prompt"), reply_markup=back_only(lang))
        return

    data = await state.get_data()
    title = data.get("habit_title", "")
    await state.clear()

    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        await habit_svc.create(session, user.id, title, remind_time)
        await session.commit()
        lang = user.language_code

    await message.answer(t(lang, "habit_created"), reply_markup=main_menu(lang))


@router.callback_query(lambda c: c.data and c.data.startswith("habit_") and c.data != "habit_name")
async def cb_habit_detail(cb: CallbackQuery) -> None:
    await cb.answer()
    habit_id = int(cb.data.split("_")[1])
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code
        user_id = user.id
        habit = await habit_svc.get_by_id(session, habit_id)
    if not habit or habit.user_id != user_id:
        await cb.message.edit_text(t(lang, "btn_my_habits"), reply_markup=back_only(lang))
        return
    text = f"{habit.title} — {habit.remind_time.strftime('%H:%M')}"
    await cb.message.edit_text(text, reply_markup=back_only(lang))


@router.callback_query(lambda c: c.data == "my_habits")
async def cb_my_habits(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        from sqlalchemy import select
        from app.models import User
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code
        habit_list = await habit_svc.get_user_habits(session, user.id)
    if not habit_list:
        from app.keyboards import back_only
        await cb.message.edit_text(t(lang, "btn_my_habits") + "\n\nNo habits yet.", reply_markup=back_only(lang))
        return
    from app.keyboards import habits_list
    hs = [(h.id, h.title) for h in habit_list]
    await cb.message.edit_text(t(lang, "btn_my_habits"), reply_markup=habits_list(hs, lang))
