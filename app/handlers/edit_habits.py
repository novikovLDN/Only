"""Edit habits — list, toggle days, change time, delete."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n.loader import get_weekdays

router = Router(name="edit_habits")


async def show_edit_habits(message: Message, user, t, session) -> None:
    from app.repositories.habit_repo import HabitRepository
    from app.keyboards.reply import main_menu

    habit_repo = HabitRepository(session)
    habits = await habit_repo.get_user_habits(user.id)
    if not habits:
        await message.answer(t("no_habits"), reply_markup=main_menu(t))
        return
    rows = []
    for h in habits:
        rows.append([InlineKeyboardButton(text=h.title, callback_data=f"edit_habit_{h.id}")])
    rows.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    await message.answer(t("edit_habits"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("edit_habit_"))
async def edit_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if not habit or habit.user_id != user.id:
        await callback.answer()
        return
    weekdays = get_weekdays(user.language)
    days_str = ", ".join(weekdays[d.weekday] for d in habit.days)
    times_str = ", ".join(f"{t.time.hour:02d}:{t.time.minute:02d}" for t in habit.times)
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
    await show_edit_habits(callback.message, user, t, session)
    await callback.answer()


@router.callback_query(F.data.startswith("del_habit_"))
async def delete_habit(callback: CallbackQuery, user, t, session) -> None:
    habit_id = int(callback.data.split("_")[2])
    from app.repositories.habit_repo import HabitRepository
    from app.keyboards.reply import main_menu

    habit_repo = HabitRepository(session)
    habit = await habit_repo.get_by_id(habit_id)
    if habit and habit.user_id == user.id:
        await habit_repo.delete(habit)
        await session.commit()
    await callback.message.edit_text(t("habit_deleted"))
    await callback.message.answer(t("welcome", username=user.first_name or "User"), reply_markup=main_menu(t))
    await callback.answer()
