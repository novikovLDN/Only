"""Confirm/Decline habit flow — inline keyboards only."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import habit_confirm_decline, decline_reasons, main_menu
from app.utils.i18n import t

router = Router(name="habit_response")


@router.callback_query(F.data.startswith("habit_confirm:"))
async def cb_habit_confirm(cb: CallbackQuery, user, t, session) -> None:
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.services.progress_service import ProgressService

    await cb.answer()
    log_id = int((cb.data or "").split(":")[1])
    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_by_id(log_id)
    if not pending or pending.user_id != user.id or pending.status != "pending":
        await cb.message.edit_text(
            "🎉\n\n" + t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
        return
    await log_repo.mark_completed(pending)
    progress_svc = ProgressService(session)
    await progress_svc.recalc_daily_for_user(user.id, pending.date)
    await session.commit()
    await cb.message.edit_text(
        "🎉\n\n" + t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
        reply_markup=main_menu(t),
    )


@router.callback_query(F.data.startswith("habit_decline:"))
async def cb_habit_decline(cb: CallbackQuery, user, t) -> None:
    await cb.answer()
    log_id = int((cb.data or "").split(":")[1])
    await cb.message.edit_text(t("decline.are_you_sure"), reply_markup=decline_reasons(t, log_id))


@router.callback_query(F.data.startswith("habit_decline_back:"))
async def cb_habit_decline_back(cb: CallbackQuery, user, t, session) -> None:
    from app.repositories.habit_repo import HabitRepository
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.services.motivation_service import MotivationService
    from app.repositories.motivation_repo import MotivationRepository

    await cb.answer()
    log_id = int((cb.data or "").split(":")[1])
    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_by_id(log_id)
    if not pending:
        text = t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
        await cb.message.edit_text(text, reply_markup=main_menu(t))
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
    await cb.message.edit_text(msg, reply_markup=habit_confirm_decline(t, pending.id))


@router.callback_query(F.data.startswith("habit_decline_tired:"))
@router.callback_query(F.data.startswith("habit_decline_sick:"))
@router.callback_query(F.data.startswith("habit_decline_no_want:"))
async def cb_habit_decline_reason(cb: CallbackQuery, user, t, session) -> None:
    from app.repositories.habit_log_repo import HabitLogRepository
    from app.services.progress_service import ProgressService

    await cb.answer()
    parts = (cb.data or "").split(":")
    if len(parts) < 2:
        return
    log_id = int(parts[1])
    reason = parts[0].replace("habit_decline_", "")
    log_repo = HabitLogRepository(session)
    pending = await log_repo.get_by_id(log_id)
    if not pending or pending.user_id != user.id:
        text = t("decline.understood") + "\n\n" + t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
        await cb.message.edit_text(text, reply_markup=main_menu(t))
        return
    await log_repo.mark_declined(pending, reason)
    progress_svc = ProgressService(session)
    await progress_svc.recalc_daily_for_user(user.id, pending.date)
    await session.commit()
    text = t("decline.understood") + "\n\n" + t("main.greeting", first_name=user.first_name or "User") + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")
    await cb.message.edit_text(text, reply_markup=main_menu(t))
