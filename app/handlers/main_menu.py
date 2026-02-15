"""Main menu — callback-based, edit_text preferred."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import main_menu as main_menu_kb

router = Router(name="main_menu")


def _welcome(user, t) -> str:
    return t("welcome", username=user.first_name or "User")


@router.callback_query(F.data == "add_habit")
async def add_habit_cb(callback: CallbackQuery, user, t, is_premium: bool = False) -> None:
    from app.handlers.habits import _presets_keyboard

    await callback.message.edit_text(
        t("select_presets"),
        reply_markup=_presets_keyboard(user, t, is_premium),
    )
    await callback.answer()


@router.callback_query(F.data == "edit_habits")
async def edit_habits_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.edit_habits import _build_edit_habits_content

    text, kb = await _build_edit_habits_content(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "loyalty")
async def loyalty_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.loyalty import _get_loyalty_content

    text, kb = await _get_loyalty_content(user, t, session, callback.message.bot)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_cb(callback: CallbackQuery, user, t) -> None:
    from app.handlers.settings import _get_settings_content

    text, kb = _get_settings_content(user, t)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_main_cb(callback: CallbackQuery, user, t, state=None) -> None:
    if state:
        await state.clear()
    await callback.message.edit_text(
        _welcome(user, t),
        reply_markup=main_menu_kb(user.language or "en", t),
    )
    await callback.answer()
