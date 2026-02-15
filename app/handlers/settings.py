"""Settings."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import settings_menu, language_select_with_back

router = Router(name="settings")


@router.callback_query(F.data == "settings_profile")
async def profile_cb(callback: CallbackQuery, user, t, session) -> None:
    from app.handlers.profile import build_profile_content

    text, kb = await build_profile_content(user, t, session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "settings_lang")
async def language_cb(callback: CallbackQuery, user, t) -> None:
    from app.utils.i18n import lang_select_prompt

    await callback.message.edit_text(
        lang_select_prompt(),
        reply_markup=language_select_with_back(t, "settings"),
    )
    await callback.answer()
