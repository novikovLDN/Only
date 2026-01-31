"""
Notification service — send messages, schedule-aware.
"""

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from app.models.user import User
from app.models.habit import Habit


class NotificationService:
    """Send notifications to users."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send_habit_reminder(
        self,
        user: User,
        habit: Habit,
        keyboard: InlineKeyboardMarkup | None = None,
    ) -> bool:
        """Send habit reminder to user."""
        try:
            text = f"🔔 Напоминание: {habit.emoji or '✅'} {habit.name}"
            await self._bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=keyboard,
            )
            return True
        except Exception:
            return False

    async def send_trial_notification(
        self, user: User, message_type: str
    ) -> bool:
        """Send trial lifecycle notification."""
        messages = {
            "trial_36h": "⏰ Прошло 36 часов с начала триала. Как успехи с привычками?",
            "trial_90h": "📊 Половина триала позади! Продолжайте в том же духе.",
            "trial_minus_24h": "⚠️ Ваш триал заканчивается через 24 часа. Оформите подписку для продолжения.",
            "trial_minus_3h": "🚨 Триал заканчивается через 3 часа! Успейте оформить Premium.",
            "trial_expired": "😔 Триал закончился. Оформите подписку, чтобы продолжить отслеживать привычки.",
        }
        text = messages.get(message_type, "Уведомление")
        try:
            await self._bot.send_message(chat_id=user.telegram_id, text=text)
            return True
        except Exception:
            return False

    async def send_subscription_notification(
        self, user: User, message_type: str
    ) -> bool:
        """Send subscription expiry notification."""
        messages = {
            "sub_minus_3d": "📅 Подписка истекает через 3 дня. Продлите, чтобы не потерять доступ.",
            "sub_minus_24h": "⚠️ Подписка истекает через 24 часа.",
            "sub_minus_3h": "🚨 Подписка истекает через 3 часа!",
            "sub_expired": "😔 Подписка истекла. Продлите для продолжения.",
        }
        text = messages.get(message_type, "Уведомление")
        try:
            await self._bot.send_message(chat_id=user.telegram_id, text=text)
            return True
        except Exception:
            return False
