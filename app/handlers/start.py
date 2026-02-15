"""Start and language selection."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import language_select, main_menu
from app.utils.i18n import lang_select_prompt

router = Router(name="start")


def _welcome_text(t) -> str:
    return f"{t('main.greeting')}\n\n{t('main.subtitle')}\n\n{t('main.action_prompt')}"


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service) -> None:
    if user.language in ("ru", "en"):
        name = user.first_name or "User"
        await message.answer(
            t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu(t),
        )
    else:
        await message.answer(
            lang_select_prompt(),
            reply_markup=language_select(),
        )


@router.callback_query(F.data.in_(["lang_ru", "lang_en"]))
async def lang_selected(callback: CallbackQuery, user, t, session, user_service) -> None:
    from app.utils.i18n import t as i18n_t
    from app.keyboards.inline import main_menu as main_menu_kb

    lang = "ru" if callback.data == "lang_ru" else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    user.language = lang
    name = user.first_name or "User"
    _t = lambda k, **kw: i18n_t(lang, k, **kw)
    await callback.message.edit_text(
        _t("main.greeting", first_name=name) + "\n\n" + _t("main.subtitle") + "\n\n" + _t("main.action_prompt"),
        reply_markup=main_menu_kb(_t),
    )
    await callback.answer()
