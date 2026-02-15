"""Start and language selection."""

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message

from app.keyboards.reply import language_select, main_menu
from app.utils.i18n import lang_select_prompt

router = Router(name="start")

LANG_RU = "🇷🇺 Русский"
LANG_EN = "🇺🇸 English"


def _welcome_text(t, name: str = "User") -> str:
    return f"{t('main.greeting', first_name=name)}\n\n{t('main.subtitle')}\n\n{t('main.action_prompt')}"


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
            _welcome_text(t, name),
            reply_markup=main_menu(t),
        )


@router.message(StateFilter("settings:language"), F.text.in_(("🔙 Back", "🔙 Назад")))
async def back_from_lang(message: Message, user, t, state) -> None:
    from app.keyboards.reply import settings_menu
    st = await state.get_state()
    if st == "settings:language":
        await state.clear()
        await message.answer(t("settings.title"), reply_markup=settings_menu(t))


@router.message(F.text.in_([LANG_RU, LANG_EN]))
async def lang_selected(message: Message, user, t, session, user_service, state) -> None:
    from app.utils.i18n import t as i18n_t
    from app.keyboards.reply import settings_menu

    lang = "ru" if message.text == LANG_RU else "en"
    await user_service.update_language(user, lang)
    await session.commit()
    user.language = lang
    _t = lambda k, **kw: i18n_t(lang, k, **kw)
    name = user.first_name or "User"

    st = await state.get_state()
    if st == "settings:language":
        await state.clear()
        await message.answer(_t("settings.title"), reply_markup=settings_menu(_t))
    else:
        await message.answer(_welcome_text(_t, name), reply_markup=main_menu(_t))
