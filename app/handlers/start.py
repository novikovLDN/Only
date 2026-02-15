"""Start and language selection — inline only, no command menu."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.keyboards.inline import main_menu

router = Router(name="start")


def _welcome_text(username: str, t) -> str:
    return t("welcome", username=username or "User")


def _lang_select_text() -> str:
    return "Выберите язык / Choose language"


def _lang_select_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service) -> None:
    if user.language in ("ru", "en"):
        await message.answer(
            _welcome_text(user.first_name or "User", t),
            reply_markup=main_menu(user.language, t),
        )
    else:
        await message.answer(
            _lang_select_text(),
            reply_markup=_lang_select_markup(),
        )


@router.callback_query(F.data.in_(["lang_ru", "lang_en"]))
async def lang_selected(callback: CallbackQuery, user, t, session, user_service) -> None:
    lang = "ru" if callback.data == "lang_ru" else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    await callback.message.edit_text(
        _welcome_text(user.first_name or "User", t),
        reply_markup=main_menu(lang, t),
    )
    await callback.answer()
