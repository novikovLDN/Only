"""Settings handler."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import language_select, settings_menu

router = Router(name="settings")


async def show_settings(message: Message, user, t) -> None:
    await message.answer(t("settings"), reply_markup=settings_menu(t))


@router.callback_query(F.data == "settings_profile")
async def settings_profile_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.profile import show_profile
    try:
        await callback.message.delete()
    except Exception:
        pass
    msg = callback.message
    await show_profile(msg, user, t, session)
    await callback.answer()


@router.callback_query(F.data == "settings_lang")
async def settings_lang_cb(callback: CallbackQuery, user, t) -> None:
    try:
        await callback.message.edit_text(t("choose_language"), reply_markup=language_select())
    except Exception:
        await callback.message.answer(t("choose_language"), reply_markup=language_select())
    await callback.answer()
