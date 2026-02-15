"""Settings handler — reply keyboard."""

from aiogram import Router, F
from aiogram.types import Message

from app.keyboards.reply import settings_kb, main_menu_kb, language_select_kb

router = Router(name="settings")

_PROFILE = ["👤 Профиль", "👤 Profile"]
_LANGUAGE = ["🌐 Язык", "🌐 Language"]


async def show_settings(message: Message, user, t) -> None:
    await message.answer(t("settings"), reply_markup=settings_kb(user.language))


@router.message(F.text.in_(_PROFILE))
async def profile_route(message: Message, user, t, session) -> None:
    from app.handlers.profile import show_profile

    await show_profile(message, user, t, session)


@router.message(F.text.in_(_LANGUAGE))
async def language_route(message: Message, user, t) -> None:
    await message.answer(t("choose_language"), reply_markup=language_select_kb())
