"""Confirm/Decline habit flow — Message handlers for ReplyKeyboard buttons."""

import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import Message

from app.utils.i18n import t, text_to_decline_reason, TRANSLATIONS
from app.keyboards.reply import habit_confirm_decline, decline_reasons, remove_reply_keyboard
from app.keyboards.inline import main_menu

logger = logging.getLogger(__name__)
router = Router(name="habit_response")

CONFIRM_TEXTS = frozenset([
    TRANSLATIONS["ru"]["btn.confirm"], TRANSLATIONS["en"]["btn.confirm"],
])
DECLINE_TEXTS = frozenset([
    TRANSLATIONS["ru"]["btn.decline"], TRANSLATIONS["en"]["btn.decline"],
])
DECLINE_BACK_TEXTS = frozenset([
    TRANSLATIONS["ru"]["decline.back"], TRANSLATIONS["en"]["decline.back"],
])
DECLINE_REASON_TEXTS = frozenset([
    TRANSLATIONS["ru"]["decline.reason_tired"], TRANSLATIONS["en"]["decline.reason_tired"],
    TRANSLATIONS["ru"]["decline.reason_sick"], TRANSLATIONS["en"]["decline.reason_sick"],
    TRANSLATIONS["ru"]["decline.reason_no_want"], TRANSLATIONS["en"]["decline.reason_no_want"],
])


@router.message(F.text.in_(CONFIRM_TEXTS))
async def confirm_habit(message: Message, user, t, session) -> None:
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.services.progress_service import ProgressService

    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_pending_for_user(user.id)
    if not pending:
        await message.answer("🎉", reply_markup=remove_reply_keyboard())
        await message.answer(
            t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
        return
    await log_repo.mark_completed(pending)
    progress_svc = ProgressService(session)
    await progress_svc.recalc_daily_for_user(user.id, pending.date)
    await session.commit()
    await message.answer("🎉", reply_markup=remove_reply_keyboard())
    await message.answer(
        t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
        reply_markup=main_menu(t),
    )


@router.message(F.text.in_(DECLINE_TEXTS))
async def decline_habit(message: Message, user, t) -> None:
    await message.answer(
        t("decline.are_you_sure"),
        reply_markup=decline_reasons(t),
    )


@router.message(F.text.in_(DECLINE_BACK_TEXTS))
async def decline_back(message: Message, user, t, session) -> None:
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.repositories.habit_repo import HabitRepository
    from app.services.motivation_service import MotivationService
    from app.repositories.motivation_repo import MotivationRepository

    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_pending_for_user(user.id)
    if not pending:
        await message.answer(
            t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
        return
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(pending.habit_id)
    if not habit:
        return
    lang = user.language if user.language in ("ru", "en") else "ru"
    motivation_repo = MotivationRepository(session)
    motivation_svc = MotivationService(motivation_repo)
    phrase = await motivation_svc.get_random_phrase(lang)
    await session.commit()
    msg = f"📌 {habit.title}\n\n{phrase}"
    await message.answer(msg, reply_markup=habit_confirm_decline(t))


@router.message(F.text.in_(DECLINE_REASON_TEXTS))
async def decline_reason_selected(message: Message, user, t, session) -> None:
    reason = text_to_decline_reason(message.text or "")
    if not reason:
        return
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.services.progress_service import ProgressService

    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_pending_for_user(user.id)
    if not pending:
        await message.answer(t("decline.understood"), reply_markup=remove_reply_keyboard())
        await message.answer(
            t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
        return
    await log_repo.mark_declined(pending, reason)
    progress_svc = ProgressService(session)
    await progress_svc.recalc_daily_for_user(user.id, pending.date)
    await session.commit()
    await message.answer(t("decline.understood"), reply_markup=remove_reply_keyboard())
    await message.answer(
        t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
        reply_markup=main_menu(t),
    )
