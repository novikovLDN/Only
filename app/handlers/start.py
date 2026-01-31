"""
Start and main menu handlers.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.main_menu import main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user) -> None:
    """Handle /start. Referral applied in middleware if new user."""
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу тебе отслеживать привычки и напоминать о них.\n\n"
        "Используй меню ниже:"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    """Settings placeholder."""
    await message.answer("⚙️ Настройки: уведомления, часовой пояс — скоро!")


@router.message(F.text == "💳 Баланс")
async def balance_handler(message: Message, user, session) -> None:
    """Balance placeholder."""
    from app.repositories.balance_repo import BalanceRepository

    repo = BalanceRepository(session)
    bal = await repo.get_or_create(user.id)
    await message.answer(f"💰 Баланс: {bal.amount} {bal.currency}")


@router.message(F.text == "👥 Рефералы")
async def referrals_handler(message: Message, user) -> None:
    """Referral link."""
    bot = message.bot
    me = await bot.me()
    username = me.username if me else "your_bot"
    link = f"https://t.me/{username}?start=ref_{user.referral_code}" if user and user.referral_code else "—"
    await message.answer(f"👥 Твоя реферальная ссылка:\n{link}")


@router.message(F.text == "📋 Мои привычки")
async def my_habits(message: Message, user, session) -> None:
    """Show user habits."""
    from app.repositories.habit_repo import HabitRepository
    from app.keyboards.habits import habits_list_keyboard

    repo = HabitRepository(session)
    habits = await repo.get_user_habits(user.id)
    if not habits:
        await message.answer("У тебя пока нет привычек. Добавь первую! ➕")
        return
    text = "📋 Твои привычки:\n\nВыбери привычку:"
    await message.answer(text, reply_markup=habits_list_keyboard(habits))
