"""
Start and main menu handlers.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.keyboards.main_menu import main_menu_keyboard
from app.texts import (
    BALANCE_LABEL,
    BALANCE_TOPUP_CTA,
    REFERRAL_INTRO,
    SETTINGS_COMING,
    WELCOME,
)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user, state: FSMContext) -> None:
    """Сброс FSM при /start — пользователь не застревает в старом flow."""
    await state.clear()
    name = message.from_user.first_name or "друг"
    await message.answer(WELCOME.format(name=name), reply_markup=main_menu_keyboard())


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    """Settings placeholder."""
    await message.answer(SETTINGS_COMING)


@router.message(F.text == "💳 Баланс")
async def balance_handler(message: Message, user, session) -> None:
    """Balance + кнопка пополнения."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    from app.repositories.balance_repo import BalanceRepository

    repo = BalanceRepository(session)
    bal = await repo.get_or_create(user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BALANCE_TOPUP_CTA, callback_data="balance_topup")],
    ])
    await message.answer(BALANCE_LABEL.format(amount=bal.amount, currency=bal.currency), reply_markup=kb)


@router.message(F.text == "👥 Рефералы")
async def referrals_handler(message: Message, user) -> None:
    """Referral link."""
    bot = message.bot
    me = await bot.me()
    username = me.username if me else "your_bot"
    link = f"https://t.me/{username}?start=ref_{user.referral_code}" if user and user.referral_code else "—"
    await message.answer(REFERRAL_INTRO.format(link=link))


@router.message(F.text == "📋 Мои привычки")
async def my_habits(message: Message, user, session) -> None:
    """Show user habits."""
    from app.keyboards.habits import habits_list_keyboard
    from app.repositories.habit_repo import HabitRepository
    from app.texts import HABITS_EMPTY, HABITS_LIST_TITLE

    repo = HabitRepository(session)
    habits = await repo.get_user_habits(user.id)
    if not habits:
        await message.answer(HABITS_EMPTY)
        return
    await message.answer(HABITS_LIST_TITLE, reply_markup=habits_list_keyboard(habits))
