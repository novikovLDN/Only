"""2328 Crypto webhook handler."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Request, Response
from aiogram import Bot

from app.config import settings
from app.db import get_session_maker
from app.services.crypto_service import process_crypto_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@asynccontextmanager
async def _get_bot():
    """Create bot instance for sending notifications (webhook runs in separate process)."""
    bot = Bot(token=settings.bot_token) if settings.bot_token else None
    try:
        yield bot
    finally:
        if bot:
            await bot.session.close()


@router.post("/crypto")
async def crypto_webhook(request: Request) -> Response:
    """
    2328.io webhook. Verify HMAC, process paid/overpaid, activate Premium.
    Always return 200 quickly (except 401 on invalid sign).
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.warning("Crypto webhook invalid JSON: %s", e)
        return Response(status_code=400)

    logger.info("Crypto webhook received: uuid=%s status=%s", body.get("uuid"), body.get("payment_status"))

    sm = get_session_maker()
    async with sm() as session:
        async with _get_bot() as bot:
            status_code, _ = await process_crypto_webhook(session, body, bot=bot)
        await session.commit()

    return Response(status_code=status_code)
