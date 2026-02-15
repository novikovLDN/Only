"""Start and language selection."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import language_select, main_menu
from app.keyboards.reply import main_menu_reply
from app.utils.i18n import lang_select_prompt

router = Router(name="start")


def _welcome_text(t) -> str:
    return f"{t('main.greeting')}\n\n{t('main.subtitle')}\n\n{t('main.action_prompt')}"


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, session, user_service, **kwargs) -> None:
    user_just_created = kwargs.get("user_just_created", False)
    if user_just_created or user.language not in ("ru", "en"):
        await message.answer(
            lang_select_prompt(),
            reply_markup=language_select(),
        )
    else:
        name = user.first_name or "User"
        await message.answer(
            t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt"),
            reply_markup=main_menu_reply(t),
        )


@router.callback_query(F.data.regexp(r"^lang_(ru|en)(_settings)?$"))
async def lang_selected(callback: CallbackQuery, user, t, session, user_service) -> None:
    from app.utils.i18n import t as i18n_t
    from app.keyboards.inline import settings_menu

    lang = "ru" if "ru" in callback.data else "en"
    return_to_settings = "_settings" in callback.data
    await user_service.update_language(user, lang)
    await session.commit()
    user.language = lang
    _t = lambda k, **kw: i18n_t(lang, k, **kw)
    if return_to_settings:
        await callback.message.edit_text(
            _t("settings.title"),
            reply_markup=settings_menu(_t),
        )
    else:
        name = user.first_name or "User"
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            _t("main.greeting", first_name=name) + "\n\n" + _t("main.subtitle") + "\n\n" + _t("main.action_prompt"),
            reply_markup=main_menu_reply(_t),
        )
    await callback.answer()
