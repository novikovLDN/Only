"""Bot entrypoint."""

import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.logger import setup_logging
from app.health_server import on_startup as health_on_startup, on_shutdown as health_on_shutdown

from app.middlewares.user_context import UserContextMiddleware
from app.middlewares.subscription import SubscriptionMiddleware
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.logging_mw import LoggingMiddleware

from app.handlers import start, main_menu, habits, edit_habits, loyalty, profile, subscription, settings as settings_handler

logger = logging.getLogger(__name__)
_bot_ref = {}


async def _on_startup(bot: Bot) -> None:
    await health_on_startup(bot, _bot_ref)


async def _on_shutdown(bot: Bot) -> None:
    await health_on_shutdown(bot, _bot_ref)


def main() -> None:
    setup_logging()
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(habits.router)
    dp.include_router(edit_habits.router)
    dp.include_router(loyalty.router)
    dp.include_router(profile.router)
    dp.include_router(subscription.router)
    dp.include_router(settings_handler.router)
    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
