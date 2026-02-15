"""Main menu."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import main_menu as main_menu_kb

router = Router(name="main_menu")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


@router.callback_query(F.data == "back_main")
async def back_main_cb(callback: CallbackQuery, user, t, state=None) -> None:
    if state:
        await state.clear()
    await callback.message.edit_text(
        _welcome(user, t),
        reply_markup=main_menu_kb(t),
    )
    await callback.answer()


@router.callback_query(F.data == "add_habit")
async def add_habit_cb(callback: CallbackQuery, user, t, is_premium: bool = False, state=None) -> None:
    from app.handlers.habits import show_presets_screen
    from app.fsm.states import AddHabitStates

    if state:
        await state.set_state(AddHabitStates.presets)
        await state.update_data(preset_page=0, preset_selected=[])
    await show_presets_screen(callback, user, t, is_premium, page=0, selected=frozenset(), state=state)
    await callback.answer()


@router.callback_query(F.data == "edit_habits")
async def edit_habits_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.edit_habits import build_edit_habits_screen

    text, kb = await build_edit_habits_screen(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "loyalty")
async def loyalty_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.loyalty import build_loyalty_content

    text, kb = await build_loyalty_content(user, t, session, callback.message.bot)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_cb(callback: CallbackQuery, user, t) -> None:
    from app.keyboards.inline import settings_menu

    await callback.message.edit_text(t("settings.title"), reply_markup=settings_menu(t))
    await callback.answer()
