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


@router.callback_query(F.data == "support")
async def support_cb(callback: CallbackQuery, user, t) -> None:
    from app.keyboards.inline import back_only

    await callback.message.edit_text(
        t("support_contact"),
        reply_markup=back_only(t, "back_main"),
    )
    await callback.answer()


@router.callback_query(F.data == "settings_lang")
async def language_cb(callback: CallbackQuery, user, t) -> None:
    await callback.message.edit_text(t("change_language"), reply_markup=language_select_with_back(t, "settings"))
    await callback.answer()
