"""Start and language selection handlers."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import language_select
from app.keyboards.reply import main_menu

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service) -> None:
    await message.answer(
        "Choose language / Выбери язык:",
        reply_markup=language_select(),
    )


@router.callback_query(F.data.in_(["lang_ru", "lang_en"]))
async def lang_selected(callback: CallbackQuery, user, t, session, user_service) -> None:
    lang = "ru" if callback.data == "lang_ru" else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        t("welcome", username=user.first_name or "User"),
        reply_markup=main_menu(t),
    )
    await callback.answer()
