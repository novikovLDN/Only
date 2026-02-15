"""Command handlers: /add, /edit, /support, /subscribe, /loyalty."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.inline import presets_page, tariff_select
from app.keyboards.reply import main_menu_reply

SUPPORT_URL = "https://t.me/asc_support"

# Reply keyboard button texts (RU, EN) for routing
BTN_ADD = ("➕ Add habit", "➕ Добавить привычку")
BTN_EDIT = ("✏️ Edit habits", "✏️ Редактировать привычки")
BTN_SUPPORT = ("🛟 Support", "🛟 Поддержка")
BTN_SUBSCRIBE = ("💎 Subscribe", "💎 Подписка")
BTN_LOYALTY = ("🎁 Loyalty program", "🎁 Программа лояльности")
BTN_SETTINGS = ("⚙️ Settings", "⚙️ Настройки")

router = Router(name="commands")


def _habit_text(t) -> str:
    return t("preset.choose_title") + "\n\n" + t("preset.choose_subtitle")


@router.message(Command("add"))
async def cmd_add(message: Message, user, t, is_premium: bool, state=None) -> None:
    from app.fsm.states import AddHabitStates

    lang = user.language or "ru"
    if state:
        await state.set_state(AddHabitStates.presets)
        await state.update_data(current_page=0, selected_habits=[])
    await message.answer(
        _habit_text(t),
        reply_markup=presets_page(t, lang, 0, set(), is_premium),
    )
    await message.answer(
        t("main.action_prompt"),
        reply_markup=main_menu_reply(t),
    )


@router.message(Command("edit"))
async def cmd_edit(message: Message, user, t, session) -> None:
    from app.handlers.edit_habits import build_edit_habits_screen

    text, kb = await build_edit_habits_screen(user, t, session)
    await message.answer(text, reply_markup=kb)
    await message.answer(
        t("main.action_prompt"),
        reply_markup=main_menu_reply(t),
    )


@router.message(Command("support"))
async def cmd_support(message: Message, t) -> None:
    await message.answer(
        f"{t('btn.support')}: {SUPPORT_URL}",
        reply_markup=main_menu_reply(t),
    )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, t) -> None:
    await message.answer(
        t("subscription.choose_tariff"),
        reply_markup=tariff_select(t),
    )
    await message.answer(
        t("main.action_prompt"),
        reply_markup=main_menu_reply(t),
    )


@router.message(Command("loyalty"))
async def cmd_loyalty(message: Message, user, t, session) -> None:
    from app.handlers.loyalty import build_loyalty_content

    text, kb = await build_loyalty_content(user, t, session, message.bot)
    await message.answer(text, reply_markup=kb)
    await message.answer(
        t("main.action_prompt"),
        reply_markup=main_menu_reply(t),
    )


# Reply keyboard button handlers
@router.message(F.text.in_(BTN_ADD))
async def btn_add(message: Message, user, t, is_premium: bool, state=None) -> None:
    await cmd_add(message, user, t, is_premium, state)


@router.message(F.text.in_(BTN_EDIT))
async def btn_edit(message: Message, user, t, session) -> None:
    await cmd_edit(message, user, t, session)


@router.message(F.text.in_(BTN_SUPPORT))
async def btn_support(message: Message, t) -> None:
    await cmd_support(message, t)


@router.message(F.text.in_(BTN_SUBSCRIBE))
async def btn_subscribe(message: Message, t) -> None:
    await cmd_subscribe(message, t)


@router.message(F.text.in_(BTN_LOYALTY))
async def btn_loyalty(message: Message, user, t, session) -> None:
    await cmd_loyalty(message, user, t, session)


@router.message(F.text.in_(BTN_SETTINGS))
async def btn_settings(message: Message, user, t) -> None:
    from app.keyboards.inline import settings_menu

    await message.answer(t("settings.title"), reply_markup=settings_menu(t))
    await message.answer(
        t("main.action_prompt"),
        reply_markup=main_menu_reply(t),
    )
