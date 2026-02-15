"""Start and language selection."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import language_select, main_menu

router = Router(name="start")


def _welcome_text(first_name: str, t) -> str:
    return t("welcome", first_name=first_name or "User")


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service) -> None:
    if user.language in ("ru", "en"):
        await message.answer(
            _welcome_text(user.first_name or "User", t),
            reply_markup=main_menu(t),
        )
    else:
        await message.answer(
            t("choose_language"),
            reply_markup=language_select(),
        )


@router.callback_query(F.data.in_(["lang_ru", "lang_en"]))
async def lang_selected(callback: CallbackQuery, user, t, session, user_service) -> None:
    lang = "ru" if callback.data == "lang_ru" else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    user.language = lang
    await callback.message.edit_text(
        _welcome_text(user.first_name or "User", t),
        reply_markup=main_menu(t),
    )
    await callback.answer()
