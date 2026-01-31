"""
Notification service — send messages, schedule-aware.
Retry on 429 (Too Many Requests) with backoff.
"""

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

from app.models.habit import Habit
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications to users."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def _send_with_retry(self, chat_id: int, text: str, **kwargs) -> bool:
        """Send message with retry on 429. Max 3 attempts."""
        for attempt in range(3):
            try:
                await self._bot.send_message(chat_id=chat_id, text=text, **kwargs)
                return True
            except TelegramRetryAfter as e:
                if attempt < 2:
                    delay = e.retry_after or 2
                    logger.warning("Telegram 429, retry in %ds (attempt %d/3)", delay, attempt + 1)
                    await asyncio.sleep(delay)
                else:
                    logger.warning("Telegram 429 after 3 attempts, chat_id=%s", chat_id)
                    return False
            except Exception:
                return False
        return False

    async def send_habit_reminder(
        self,
        user: User,
        habit: Habit,
        keyboard: InlineKeyboardMarkup | None = None,
    ) -> bool:
        """Send habit reminder to user."""
        from app.texts import REMINDER_EMOJI_DEFAULT, REMINDER_TEMPLATE

        emoji = habit.emoji or REMINDER_EMOJI_DEFAULT
        text = REMINDER_TEMPLATE.format(emoji=emoji, name=habit.name)
        return await self._send_with_retry(user.telegram_id, text, reply_markup=keyboard)

    async def send_trial_notification(
        self, user: User, message_type: str
    ) -> bool:
        """Send trial lifecycle notification."""
        from app.texts import (
            TRIAL_36H,
            TRIAL_90H,
            TRIAL_MINUS_24H,
            TRIAL_MINUS_3H,
            TRIAL_EXPIRED,
        )

        messages = {
            "trial_36h": TRIAL_36H,
            "trial_90h": TRIAL_90H,
            "trial_minus_24h": TRIAL_MINUS_24H,
            "trial_minus_3h": TRIAL_MINUS_3H,
            "trial_expired": TRIAL_EXPIRED,
        }
        text = messages.get(message_type, "Уведомление")
        return await self._send_with_retry(user.telegram_id, text)

    async def send_subscription_notification(
        self, user: User, message_type: str
    ) -> bool:
        """Send subscription expiry notification."""
        from app.texts import (
            SUB_EXPIRED,
            SUB_MINUS_24H,
            SUB_MINUS_3D,
            SUB_MINUS_3H,
        )

        messages = {
            "sub_minus_3d": SUB_MINUS_3D,
            "sub_minus_24h": SUB_MINUS_24H,
            "sub_minus_3h": SUB_MINUS_3H,
            "sub_expired": SUB_EXPIRED,
        }
        text = messages.get(message_type, "Уведомление")
        return await self._send_with_retry(user.telegram_id, text)

    async def send_inactivity_reminder(self, user: User) -> bool:
        """Retention: user hasn't logged habits recently."""
        from app.texts import INACTIVITY_REMINDER

        return await self._send_with_retry(user.telegram_id, INACTIVITY_REMINDER)

    async def send_streak_milestone(self, user: User, streak: int) -> bool:
        """Retention: streak reward notification."""
        from app.texts import (
            STREAK_7,
            STREAK_14,
            STREAK_30,
            STREAK_60,
            STREAK_100,
        )

        messages = {7: STREAK_7, 14: STREAK_14, 30: STREAK_30, 60: STREAK_60, 100: STREAK_100}
        text = messages.get(streak, f"{streak} дней подряд! 🎉")
        return await self._send_with_retry(user.telegram_id, text)

    async def send_renewal_success(self, user: User) -> bool:
        """Subscription renewed from balance."""
        from app.texts import RENEWAL_SUCCESS

        return await self._send_with_retry(user.telegram_id, RENEWAL_SUCCESS)

    async def send_renewal_failed_insufficient(self, user: User) -> bool:
        """Autorenew failed — insufficient balance."""
        from app.texts import RENEWAL_FAILED_INSUFFICIENT

        return await self._send_with_retry(user.telegram_id, RENEWAL_FAILED_INSUFFICIENT)
