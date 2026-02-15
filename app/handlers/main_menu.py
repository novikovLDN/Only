"""Main menu and Back routing."""

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.keyboards.reply import main_menu

router = Router(name="main_menu")

BTN_BACK = ("🔙 Back", "🔙 Назад")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


@router.message(~StateFilter("edit:detail", "edit:time"), F.text.in_(BTN_BACK))
async def back_main(message: Message, user, t, state=None) -> None:
    if state:
        await state.clear()
    await message.answer(
        _welcome(user, t),
        reply_markup=main_menu(t),
    )
