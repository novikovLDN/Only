"""Start and language selection handlers."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.reply import main_menu_kb, language_select_kb

router = Router(name="start")


def _get_welcome_text(user, t) -> str:
    return t("welcome", username=user.first_name or "User")


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service) -> None:
    if user.language in ("ru", "en"):
        await message.answer(
            _get_welcome_text(user, t),
            reply_markup=main_menu_kb(user.language),
        )
    else:
        await message.answer(
            "Choose language / Выбери язык:",
            reply_markup=language_select_kb(),
        )


@router.message(F.text.in_(["🇷🇺 Русский", "🇬🇧 English"]))
async def lang_selected(message: Message, user, t, session, user_service) -> None:
    lang = "ru" if message.text == "🇷🇺 Русский" else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    await message.answer(
        _get_welcome_text(user, t),
        reply_markup=main_menu_kb(lang),
    )
