"""
Payment provider factory.
"""

import logging
from typing import Any

from app.config import settings
from app.config.constants import PaymentProvider
from app.integrations.payments.base import BasePaymentProvider
from app.integrations.payments.cryptobot_provider import CryptoBotProvider
from app.integrations.payments.telegram_stars_provider import TelegramStarsProvider
from app.integrations.payments.yookassa_provider import YooKassaProvider

logger = logging.getLogger(__name__)


def get_provider(provider_id: str) -> BasePaymentProvider | None:
    """Get provider by id. Returns None if not configured."""
    if provider_id == PaymentProvider.YOOKASSA:
        return YooKassaProvider()
    if provider_id == PaymentProvider.TELEGRAM_STARS:
        return TelegramStarsProvider()
    if provider_id == PaymentProvider.CRYPTOBOT:
        return CryptoBotProvider()
    logger.warning("Unknown provider: %s", provider_id)
    return None


def get_available_providers() -> list[str]:
    """List configured providers."""
    available = []
    if settings.yookassa_shop_id and settings.yookassa_secret_key:
        available.append(PaymentProvider.YOOKASSA)
    if settings.bot_token:
        available.append(PaymentProvider.TELEGRAM_STARS)
    if settings.cryptobot_token:
        available.append(PaymentProvider.CRYPTOBOT)
    return available
