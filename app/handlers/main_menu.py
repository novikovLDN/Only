"""Main menu — routes to Add habit, Edit habits, Loyalty, Settings."""

from aiogram import Router, F
from aiogram.types import Message

from app.keyboards.reply import main_menu

router = Router(name="main_menu")


@router.message(F.text)
async def main_menu_router(message: Message, user, t, lang, session, is_premium: bool = False) -> None:
    from app.i18n.loader import get_texts
    texts = get_texts(lang)
    add_habit = texts.get("add_habit", "Add habit")
    edit_habits = texts.get("edit_habits", "Edit habits")
    loyalty = texts.get("loyalty_program", "Loyalty program")
    settings = texts.get("settings", "Settings")
    back = texts.get("back", "Back")

    if message.text == add_habit:
        from app.handlers.habits import show_presets
        await show_presets(message, user, t, is_premium)
    elif message.text == edit_habits:
        from app.handlers.edit_habits import show_edit_habits
        await show_edit_habits(message, user, t, session)
    elif message.text == loyalty:
        from app.handlers.loyalty import show_loyalty
        await show_loyalty(message, user, t, session)
    elif message.text == settings:
        from app.handlers.settings import show_settings
        await show_settings(message, user, t)
    elif message.text == back:
        await message.answer(t("welcome", username=user.first_name or "User"), reply_markup=main_menu(t))
    else:
        await message.answer(t("welcome", username=user.first_name or "User"), reply_markup=main_menu(t))


@router.callback_query(F.data == "back_main")
async def back_main_cb(callback, user, t, state=None) -> None:
    if state:
        await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(t("welcome", username=user.first_name or "User"), reply_markup=main_menu(t))
    await callback.answer()
