"""Bot entrypoint — FastAPI + uvicorn + long polling."""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logger import setup_logging

from app.middlewares.user_context import UserContextMiddleware
from app.middlewares.subscription import SubscriptionMiddleware
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.logging_mw import LoggingMiddleware

from app.handlers import start, main_menu, habits, edit_habits, loyalty, profile, subscription, settings as settings_handler
from app.web import router as web_router

logger = logging.getLogger(__name__)

_bot: Bot | None = None
_dp: Dispatcher | None = None
_polling_task: asyncio.Task | None = None


async def _lifespan_startup() -> None:
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        raise RuntimeError("BOT_TOKEN not set")
    asyncio.create_task(_start_bot())


async def _lifespan_shutdown() -> None:
    global _polling_task
    from app.scheduler import shutdown_scheduler
    from app.core.database import close_db

    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
    shutdown_scheduler()
    await close_db()
    logger.info("Shutdown complete")


def _create_bot_and_dp() -> tuple[Bot, Dispatcher]:
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
    return bot, dp


async def _start_bot() -> None:
    global _bot, _dp, _polling_task
    from app.core.database import init_db
    from app.scheduler import setup_scheduler

    await init_db()
    _bot, _dp = _create_bot_and_dp()

    async def on_startup(bot: Bot) -> None:
        setup_scheduler(bot)
        logger.info("Bot started")

    async def on_shutdown(bot: Bot) -> None:
        from app.scheduler import shutdown_scheduler
        from app.core.database import close_db

        shutdown_scheduler()
        await close_db()
        logger.info("Bot stopped")

    _dp.startup.register(on_startup)
    _dp.shutdown.register(on_shutdown)

    _polling_task = asyncio.create_task(_dp.start_polling(_bot))
    await _polling_task


@asynccontextmanager
async def _lifespan(app: FastAPI):
    await _lifespan_startup()
    yield
    await _lifespan_shutdown()


fastapi_app = FastAPI(lifespan=_lifespan)
fastapi_app.include_router(web_router)


def main() -> None:
    setup_logging()
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "app.main:fastapi_app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
