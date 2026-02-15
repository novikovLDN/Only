"""Bot entrypoint — pure long-polling."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import settings
from app.logger import setup_logging

from app.middlewares.user_context import UserContextMiddleware
from app.middlewares.subscription import SubscriptionMiddleware
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.logging_mw import LoggingMiddleware

from app.handlers import start, main_menu, habits, edit_habits, loyalty, profile, subscription, settings as settings_handler
from app.handlers import habit_response, commands, callbacks

logger = logging.getLogger(__name__)

def _create_bot_and_dp() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.pre_checkout_query.middleware(LoggingMiddleware())
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    dp.pre_checkout_query.middleware(UserContextMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.pre_checkout_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.include_router(callbacks.router)
    dp.include_router(habit_response.router)
    dp.include_router(start.router)
    dp.include_router(commands.router)
    dp.include_router(habits.router)
    dp.include_router(edit_habits.router)
    dp.include_router(main_menu.router)
    dp.include_router(loyalty.router)
    dp.include_router(profile.router)
    dp.include_router(subscription.router)
    dp.include_router(settings_handler.router)
    return bot, dp


async def main() -> None:
    from app.core.database import init_db, close_db, run_migrations
    from app.scheduler import setup_scheduler, shutdown_scheduler

    setup_logging()
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)

    _url = settings.database_url
    _safe = _url.split("@")[-1] if "@" in _url else "***"
    logger.info("DATABASE_URL (host): %s", _safe)

    try:
        run_migrations()
    except Exception as e:
        logger.exception("Migration failed: %s", e)
        sys.exit(1)

    await init_db()
    bot, dp = _create_bot_and_dp()
    # No set_my_commands — inline keyboards only, no persistent menu
    setup_scheduler(bot)

    try:
        await dp.start_polling(bot)
    finally:
        shutdown_scheduler()
        await close_db()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
