"""Settings handler — inline only."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import settings_menu, main_menu, language_select

router = Router(name="settings")


async def show_settings(message: Message, user, t) -> None:
    lang = user.language or "en"
    await message.answer(t("settings"), reply_markup=settings_menu(lang, t))


@router.callback_query(F.data == "settings_profile")
async def profile_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.profile import show_profile
    try:
        await callback.message.delete()
    except Exception:
        pass
    await show_profile(callback.message, user, t, session)
    await callback.answer()


@router.callback_query(F.data == "settings_lang")
async def language_cb(callback: CallbackQuery, user, t) -> None:
    lang = user.language or "en"
    await callback.message.edit_text(t("choose_language"), reply_markup=language_select(with_back=True, lang=lang))
    await callback.answer()
