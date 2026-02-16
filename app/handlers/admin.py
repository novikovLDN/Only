"""Admin dashboard — only for ADMIN_ID."""

from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select, update

from app.config import ADMIN_ID
from app.db import get_session_maker
from app.keyboards.admin import (
    admin_back_keyboard,
    admin_habits_keyboard,
    admin_main_keyboard,
    admin_user_actions_keyboard,
)
from app.models import Habit, User
from app.services import habit_service
from app.utils.time_parser import parse_admin_duration

router = Router(name="admin")


class AdminStates(StatesGroup):
    search_user = State()
    grant_duration = State()


def _is_admin(user_id: int | None) -> bool:
    return user_id == ADMIN_ID


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.message(Command("admin"))
async def admin_entry(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Ай ай ай, сюда нельзя 😉")
        return
    await message.answer(
        "🔐 Админ-панель",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    await state.clear()
    await cb.message.edit_text(
        "🔐 Админ-панель",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    sm = get_session_maker()
    async with sm() as session:
        total_users = await session.scalar(select(func.count()).select_from(User))
        now = _now_utc()
        active_subs = await session.scalar(
            select(func.count()).where(
                User.premium_until.isnot(None),
                User.premium_until > now,
            )
        )
    await cb.message.edit_text(
        f"📊 Статистика:\n\n"
        f"Всего пользователей: {total_users or 0}\n"
        f"Активных подписок: {active_subs or 0}",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin_users")
async def admin_users(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    await state.set_state(AdminStates.search_user)
    await cb.message.edit_text(
        "🔎 Введите ID или @username пользователя:",
        reply_markup=admin_back_keyboard(),
    )


@router.message(AdminStates.search_user, F.text)
async def admin_search_user(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    query = (message.text or "").strip().replace("@", "")
    if not query:
        return
    sm = get_session_maker()
    async with sm() as session:
        if query.isdigit():
            result = await session.execute(select(User).where(User.telegram_id == int(query)))
        else:
            result = await session.execute(select(User).where(User.username == query))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("❌ Пользователь не найден", reply_markup=admin_back_keyboard())
            return
        habits_count = await session.scalar(
            select(func.count()).select_from(Habit).where(Habit.user_id == user.id, Habit.is_active == True)
        )
    sub_status = "Неактивна"
    if user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > _now_utc():
            sub_status = f"Активна до {user.premium_until.strftime('%d.%m.%Y')}"
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    username_str = f"@{user.username}" if user.username else "—"
    await message.answer(
        f"👤 Пользователь:\n\n"
        f"TG ID: {user.telegram_id}\n"
        f"Username: {username_str}\n"
        f"Регистрация: {created}\n"
        f"Подписка: {sub_status}\n"
        f"Активных привычек: {habits_count or 0}",
        reply_markup=admin_user_actions_keyboard(user.telegram_id),
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_grant:"))
async def admin_grant(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tg_id = int(cb.data.split(":")[1])
    await state.update_data(admin_grant_tg_id=tg_id)
    await state.set_state(AdminStates.grant_duration)
    await cb.message.edit_text(
        "⏳ Введите срок (пример: 30d, 2m, 10h, 15min):",
        reply_markup=admin_back_keyboard(),
    )


@router.message(AdminStates.grant_duration, F.text)
async def admin_apply_grant(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    data = await state.get_data()
    tg_id = data.get("admin_grant_tg_id")
    if not tg_id:
        await state.clear()
        return
    duration = parse_admin_duration(message.text or "")
    if not duration:
        await message.answer("❌ Неверный формат. Пример: 30d, 2m, 10h")
        return
    sm = get_session_maker()
    async with sm() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("❌ Пользователь не найден")
            await state.clear()
            return
        now = _now_utc()
        if user.premium_until:
            pu = user.premium_until
            if pu.tzinfo is None:
                pu = pu.replace(tzinfo=timezone.utc)
            if pu > now:
                user.premium_until = pu + duration
            else:
                user.premium_until = now + duration
        else:
            user.premium_until = now + duration
        await session.commit()
    await message.answer("✅ Доступ выдан")
    await state.clear()


@router.callback_query(F.data.startswith("admin_revoke:"))
async def admin_revoke(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tg_id = int(cb.data.split(":")[1])
    sm = get_session_maker()
    async with sm() as session:
        await session.execute(
            update(User).where(User.telegram_id == tg_id).values(premium_until=None)
        )
        await session.commit()
    await cb.message.answer("❌ Подписка удалена")


@router.callback_query(F.data == "admin_habits")
async def admin_habits(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        result = await session.execute(select(User).where(User.telegram_id == tid))
        user = result.scalar_one_or_none()
        if not user:
            await cb.message.edit_text("❌ Пользователь не найден", reply_markup=admin_back_keyboard())
            return
        habits = await habit_service.get_user_habits(session, user.id)
    if not habits:
        await cb.message.edit_text(
            "🧪 Нет привычек",
            reply_markup=admin_back_keyboard(),
        )
        return
    hs = [(h.id, h.title) for h in habits]
    await cb.message.edit_text(
        "🧪 Удалить привычку:",
        reply_markup=admin_habits_keyboard(hs),
    )


@router.callback_query(F.data.startswith("admin_delete_habit:"))
async def admin_delete_habit(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    sm = get_session_maker()
    async with sm() as session:
        habit = await habit_service.get_by_id(session, habit_id)
        if habit:
            await habit_service.delete_habit(session, habit)
            await session.commit()
    await cb.message.answer("🗑 Привычка удалена")
