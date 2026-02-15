"""Settings handler — inline only."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import settings_menu, language_select

router = Router(name="settings")


def _get_settings_content(user, t) -> tuple[str, "settings_menu"]:
    lang = user.language or "en"
    return t("settings"), settings_menu(lang, t)


async def show_settings(message: Message, user, t) -> None:
    text, kb = _get_settings_content(user, t)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "settings_profile")
async def profile_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.profile import _get_profile_content

    text, kb = await _get_profile_content(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "settings_lang")
async def language_cb(callback: CallbackQuery, user, t) -> None:
    lang = user.language or "en"
    await callback.message.edit_text(t("choose_language"), reply_markup=language_select(with_back=True, lang=lang))
    await callback.answer()
