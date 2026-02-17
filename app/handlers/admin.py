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
from app.services import admin_service, user_service
from app.texts import _normalize_lang, t
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
    delete_user_tg_id = State()
    delete_user_confirm = State()


def _is_admin(user_id: int | None) -> bool:
    return user_id == ADMIN_ID


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.message(Command("admin"))
async def admin_entry(message: Message) -> None:
    tid = message.from_user.id if message.from_user else None
    if not _is_admin(tid):
        sm = get_session_maker()
        async with sm() as session:
            user = await user_service.get_by_telegram_id(session, tid or 0)
            lang = user.language_code if user else "ru"
        await message.answer(t(lang, "admin_denied"))
        return
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, ADMIN_ID)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await message.answer(
        t(lang, "admin_panel"),
        reply_markup=admin_main_keyboard(lang),
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    await state.clear()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await cb.message.edit_text(
        t(lang, "admin_panel"),
        reply_markup=admin_main_keyboard(lang),
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
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
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await cb.message.edit_text(
        f"{t(lang, 'admin_stats_title')}\n\n"
        f"{t(lang, 'admin_stats_users')}: {total_users or 0}\n"
        f"{t(lang, 'admin_stats_subs')}: {active_subs or 0}",
        reply_markup=admin_main_keyboard(lang),
    )


@router.callback_query(F.data == "admin_users")
async def admin_users(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await state.set_state(AdminStates.search_user)
    await cb.message.edit_text(
        t(lang, "admin_search_prompt"),
        reply_markup=admin_back_keyboard(lang),
    )


@router.message(AdminStates.search_user, F.text)
async def admin_search_user(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    query = (message.text or "").strip().replace("@", "")
    if not query:
        return
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        if query.isdigit():
            result = await session.execute(select(User).where(User.telegram_id == int(query)))
        else:
            result = await session.execute(select(User).where(User.username == query))
        user = result.scalar_one_or_none()
        if not user:
            admin_user = await user_service.get_by_telegram_id(session, tid)
            lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
            await message.answer(t(lang, "admin_user_not_found"), reply_markup=admin_back_keyboard(lang))
            return
        habits_count = await session.scalar(
            select(func.count()).select_from(Habit).where(Habit.user_id == user.id, Habit.is_active == True)
        )
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    sub_status = t(lang, "admin_sub_no")
    if user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > _now_utc():
            sub_status = t(lang, "admin_sub_active", date=user.premium_until.strftime("%d.%m.%Y"))
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    username_str = f"@{user.username}" if user.username else "—"
    await message.answer(
        f"👤 {t(lang, 'admin_user_label')}:\n\n"
        f"TG ID: {user.telegram_id}\n"
        f"Username: {username_str}\n"
        f"{t(lang, 'admin_reg_label')}: {created}\n"
        f"{t(lang, 'admin_sub_label')}: {sub_status}\n"
        f"{t(lang, 'admin_habits_label')}: {habits_count or 0}",
        reply_markup=admin_user_actions_keyboard(user.telegram_id, lang),
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_grant:"))
async def admin_grant(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tg_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await state.update_data(admin_grant_tg_id=tg_id)
    await state.set_state(AdminStates.grant_duration)
    await cb.message.edit_text(
        t(lang, "admin_grant_prompt"),
        reply_markup=admin_back_keyboard(lang),
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
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    if not duration:
        await message.answer(t(lang, "admin_invalid_format"))
        return
    async with sm() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(t(lang, "admin_user_not_found"))
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
    await message.answer(t(lang, "admin_grant_ok"))
    await state.clear()


@router.callback_query(F.data.startswith("admin_revoke:"))
async def admin_revoke(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    tg_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        await session.execute(
            update(User).where(User.telegram_id == tg_id).values(premium_until=None)
        )
        await session.commit()
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await cb.message.answer(t(lang, "admin_sub_revoked"))


@router.callback_query(F.data == "admin_delete_user")
async def admin_delete_user_start(cb: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        await cb.answer(t("ru", "admin_denied"), show_alert=True)
        return
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await state.set_state(AdminStates.delete_user_tg_id)
    await cb.message.edit_text(
        t(lang, "admin_delete_prompt"),
        reply_markup=admin_back_keyboard(lang),
    )


@router.message(AdminStates.delete_user_tg_id, F.text)
async def admin_delete_user_tg_id(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"

    tg_id_str = (message.text or "").strip()
    if not tg_id_str.isdigit():
        await message.answer(t(lang, "admin_delete_id_invalid"))
        return

    await state.update_data(admin_delete_tg_id=int(tg_id_str))
    await state.set_state(AdminStates.delete_user_confirm)
    await message.answer(
        t(lang, "admin_delete_confirm", tg_id=tg_id_str),
    )


@router.message(AdminStates.delete_user_confirm, F.text)
async def admin_delete_user_execute(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"

    confirm_keyword = t(lang, "admin_delete_confirm_keyword")
    if (message.text or "").strip() != confirm_keyword:
        await message.answer(t(lang, "admin_delete_cancelled"))
        await state.clear()
        return

    data = await state.get_data()
    tg_id = data.get("admin_delete_tg_id")
    await state.clear()

    if not tg_id:
        await message.answer(t(lang, "admin_delete_not_found"))
        return

    success = await admin_service.delete_user_full_by_tg_id(tg_id)
    if success:
        await message.answer(t(lang, "admin_delete_done"))
    else:
        await message.answer(t(lang, "admin_delete_not_found"))


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
        lang = _normalize_lang(user.language_code) if user else "ru"
        if not user:
            await cb.message.edit_text(t(lang, "admin_user_not_found"), reply_markup=admin_back_keyboard(lang))
            return
        habits = await habit_service.get_user_habits(session, user.id)
    if not habits:
        await cb.message.edit_text(
            t(lang, "admin_no_habits"),
            reply_markup=admin_back_keyboard(lang),
        )
        return
    hs = [(h.id, h.title) for h in habits]
    await cb.message.edit_text(
        t(lang, "admin_delete_habit_title"),
        reply_markup=admin_habits_keyboard(hs, lang),
    )


@router.callback_query(F.data.startswith("admin_delete_habit:"))
async def admin_delete_habit(cb: CallbackQuery) -> None:
    if not _is_admin(cb.from_user.id if cb.from_user else None):
        return
    await cb.answer()
    habit_id = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        habit = await habit_service.get_by_id(session, habit_id)
        if habit:
            await habit_service.delete_habit(session, habit)
            await session.commit()
        admin_user = await user_service.get_by_telegram_id(session, tid)
        lang = _normalize_lang(admin_user.language_code) if admin_user else "ru"
    await cb.message.answer(t(lang, "admin_habit_deleted"))
