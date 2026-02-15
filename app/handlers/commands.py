"""Command handlers and Reply keyboard button routing."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.reply import (
    main_menu,
    tariff_select,
    settings_menu,
)

SUPPORT_URL = "https://t.me/asc_support"

# Button texts for routing (RU, EN)
BTN_ADD = ("➕ Add habit", "➕ Добавить привычку")
BTN_EDIT = ("✏️ Edit habits", "✏️ Редактировать привычки")
BTN_SUPPORT = ("🛟 Support", "🛟 Поддержка")
BTN_SUBSCRIBE = ("💎 Subscribe", "💎 Подписка")
BTN_LOYALTY = ("🎁 Loyalty program", "🎁 Программа лояльности")
BTN_SETTINGS = ("⚙️ Settings", "⚙️ Настройки")
BTN_BACK = ("🔙 Back", "🔙 Назад")

router = Router(name="commands")


def _welcome(user, t) -> str:
    name = user.first_name or "User"
    return t("main.greeting", first_name=name) + "\n\n" + t("main.subtitle") + "\n\n" + t("main.action_prompt")


@router.message(Command("add"))
@router.message(F.text.in_(BTN_ADD))
async def cmd_add(message: Message, user, t, is_premium: bool, state=None) -> None:
    from app.fsm.states import AddHabitStates
    from app.handlers.habits import send_presets_screen

    lang = user.language or "ru"
    if state:
        await state.set_state(AddHabitStates.presets)
        await state.update_data(current_page=0, selected_habits=[])
    await send_presets_screen(message, user, t, is_premium, page=0)


@router.message(Command("edit"))
@router.message(F.text.in_(BTN_EDIT))
async def cmd_edit(message: Message, user, t, session) -> None:
    from app.handlers.edit_habits import send_edit_habits_screen

    await send_edit_habits_screen(message, user, t, session)


@router.message(Command("support"))
@router.message(F.text.in_(BTN_SUPPORT))
async def cmd_support(message: Message, t) -> None:
    await message.answer(
        f"{t('btn.support')}: {SUPPORT_URL}",
        reply_markup=main_menu(t),
    )


@router.message(Command("subscribe"))
@router.message(F.text.in_(BTN_SUBSCRIBE))
async def cmd_subscribe(message: Message, t) -> None:
    await message.answer(
        t("subscription.choose_tariff"),
        reply_markup=tariff_select(t),
    )


@router.message(Command("loyalty"))
@router.message(F.text.in_(BTN_LOYALTY))
async def cmd_loyalty(message: Message, user, t, session) -> None:
    from app.handlers.loyalty import send_loyalty_screen

    await send_loyalty_screen(message, user, t, session)


@router.message(Command("settings"))
@router.message(F.text.in_(BTN_SETTINGS))
async def cmd_settings(message: Message, user, t) -> None:
    await message.answer(
        t("settings.title"),
        reply_markup=settings_menu(t),
    )
