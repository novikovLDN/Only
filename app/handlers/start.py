"""Start and language selection — inline keyboards only."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.inline import language_select, main_menu
from app.utils.i18n import lang_select_prompt

router = Router(name="start")


def _welcome_text(t, name: str = "User") -> str:
    return f"{t('main.greeting', first_name=name)}\n\n{t('main.subtitle')}\n\n{t('main.action_prompt')}"


@router.message(CommandStart())
async def cmd_start(message: Message, user, t, **kwargs) -> None:
    user_just_created = kwargs.get("user_just_created", False)
    if user_just_created or user.language not in ("ru", "en"):
        await message.answer(lang_select_prompt(), reply_markup=language_select())
    else:
        name = user.first_name or "User"
        await message.answer(_welcome_text(t, name), reply_markup=main_menu(t))
