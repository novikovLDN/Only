"""Main menu — routes via F.text."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.keyboards.reply import main_menu_kb, back_kb

router = Router(name="main_menu")

_ADD_HABIT = ["➕ Добавить привычку", "➕ Add Habit"]
_EDIT_HABITS = ["✏️ Редактировать привычки", "✏️ Edit Habits"]
_LOYALTY = ["🎁 Программа лояльности", "🎁 Loyalty Program"]
_SETTINGS = ["⚙️ Настройки", "⚙️ Settings"]
_BACK = ["⬅️ Назад", "⬅️ Back"]


def _welcome(message: Message, user, t) -> str:
    return t("welcome", username=user.first_name or "User")


@router.message(F.text.in_(_ADD_HABIT))
async def add_habit_route(message: Message, user, t, is_premium: bool = False) -> None:
    from app.handlers.habits import show_presets

    await show_presets(message, user, t, is_premium)


@router.message(F.text.in_(_EDIT_HABITS))
async def edit_habits_route(message: Message, user, t, session) -> None:
    from app.handlers.edit_habits import show_edit_habits

    await show_edit_habits(message, user, t, session)


@router.message(F.text.in_(_LOYALTY))
async def loyalty_route(message: Message, user, t, session) -> None:
    from app.handlers.loyalty import show_loyalty

    await show_loyalty(message, user, t, session)


@router.message(F.text.in_(_SETTINGS))
async def settings_route(message: Message, user, t) -> None:
    from app.handlers.settings import show_settings

    await show_settings(message, user, t)


@router.message(F.text.in_(_BACK))
async def back_route(message: Message, user, t, state=None) -> None:
    if state:
        await state.clear()
    await message.answer(_welcome(message, user, t), reply_markup=main_menu_kb(user.language))


@router.callback_query(F.data == "back_main")
async def back_main_cb(callback, user, t, state=None) -> None:
    if state:
        await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(_welcome(callback.message, user, t), reply_markup=main_menu_kb(user.language))
    await callback.answer()
