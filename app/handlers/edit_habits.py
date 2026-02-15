"""Edit habits — inline only."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n.loader import get_weekdays

router = Router(name="edit_habits")

from app.keyboards.inline import main_menu


async def _build_edit_habits_content(user, t, session) -> tuple[str, InlineKeyboardMarkup]:
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    lang = user.language or "en"
    if not habits:
        return t("no_habits"), main_menu(lang, t)
    rows = []
    for h in habits:
        rows.append([InlineKeyboardButton(text=h.title, callback_data=f"edit_habit_{h.id}")])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return t("edit_habits"), InlineKeyboardMarkup(inline_keyboard=rows)


async def show_edit_habits(message: Message, user, t, session) -> None:
    text, kb = await _build_edit_habits_content(user, t, session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("edit_habit_"))
async def edit_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    weekdays = get_weekdays(user.language or "en")
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t0.time.hour:02d}:{t0.time.minute:02d}" for t0 in habit.times)
    text = f"{habit.title}\nДни: {days_str}\nВремя: {times_str}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("change_time"), callback_data=f"chtime_{habit.id}")],
        [InlineKeyboardButton(text=t("delete_habit"), callback_data=f"del_habit_{habit.id}")],
        [InlineKeyboardButton(text=t("back"), callback_data="back_edit")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "back_edit")
async def back_edit(callback: CallbackQuery, user, t, session) -> None:
    text, kb = await _build_edit_habits_content(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("del_habit_"))
async def delete_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    lang = user.language or "en"
    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        await habit_repo.delete(habit)
        await session.commit()
    await callback.message.edit_text(
        t("welcome", username=user.first_name or "User"),
        reply_markup=main_menu(lang, t),
    )
    await callback.answer()
