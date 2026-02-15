"""Command handlers — always answer with inline keyboard."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.inline import main_menu, tariff_select, settings_menu

SUPPORT_URL = "https://t.me/asc_support"

router = Router(name="commands")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


@router.message(Command("add"))
async def cmd_add(message: Message, user, t, is_premium: bool, state=None) -> None:
    from app.fsm.states import AddHabitStates
    from app.handlers.habits import send_presets_screen

    lang = user.language or "ru"
    if state:
        await state.set_state(AddHabitStates.presets)
        await state.update_data(current_page=0, selected_habits=[])
    await send_presets_screen(message, user, t, is_premium, page=0)


@router.message(Command("edit"))
async def cmd_edit(message: Message, user, t, session) -> None:
    from app.handlers.edit_habits import send_edit_habits_screen

    await send_edit_habits_screen(message, user, t, session)


@router.message(Command("support"))
async def cmd_support(message: Message, t) -> None:
    await message.answer(f"{t('btn.support')}: {SUPPORT_URL}", reply_markup=main_menu(t))


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, t) -> None:
    await message.answer(t("subscription.choose_tariff"), reply_markup=tariff_select(t))


@router.message(Command("loyalty"))
async def cmd_loyalty(message: Message, user, t, session) -> None:
    from app.handlers.loyalty import send_loyalty_screen

    await send_loyalty_screen(message, user, t, session)


@router.message(Command("settings"))
async def cmd_settings(message: Message, t) -> None:
    await message.answer(t("settings.title"), reply_markup=settings_menu(t))
