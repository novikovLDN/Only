"""Settings — Reply keyboard only."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.reply import settings_menu, language_select_with_back
from app.utils.i18n import lang_select_prompt, TRANSLATIONS

router = Router(name="settings")

SETTINGS_BUTTONS = (
    TRANSLATIONS["ru"]["settings.my_profile"],
    TRANSLATIONS["en"]["settings.my_profile"],
    TRANSLATIONS["ru"]["settings.change_language"],
    TRANSLATIONS["en"]["settings.change_language"],
    TRANSLATIONS["ru"]["btn.support"],
    TRANSLATIONS["en"]["btn.support"],
)


@router.message(F.text.in_(SETTINGS_BUTTONS))
async def settings_nav(message: Message, user, t, session, state: FSMContext) -> None:
    text = message.text or ""

    if text in (TRANSLATIONS["ru"]["settings.my_profile"], TRANSLATIONS["en"]["settings.my_profile"]):
        from app.handlers.profile import send_profile_screen
        await send_profile_screen(message, user, t, session)
        return

    if text in (TRANSLATIONS["ru"]["settings.change_language"], TRANSLATIONS["en"]["settings.change_language"]):
        await state.set_state("settings:language")
        await message.answer(
            lang_select_prompt(),
            reply_markup=language_select_with_back(t),
        )
        return

    if text in (TRANSLATIONS["ru"]["btn.support"], TRANSLATIONS["en"]["btn.support"]):
        from app.keyboards.reply import main_menu
        await message.answer(
            f"{t('btn.support')}: https://t.me/asc_support",
            reply_markup=main_menu(t),
        )
        return
        return
