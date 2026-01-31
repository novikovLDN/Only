"""
Webhook processor — verify, parse, route to PaymentService.
"""

import json
import logging
from typing import Any

from app.config.constants import PaymentProvider
from app.integrations.payment_service import PaymentService
from app.integrations.payments.providers import get_provider

logger = logging.getLogger(__name__)


async def process_yookassa_webhook(
    service: PaymentService,
    body: bytes,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    """
    Process YooKassa webhook. Returns (status_code, response_body).
    """
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON: %s", e)
        return 400, "Invalid JSON"
    signature = headers.get("X-Signature", "") if headers else None
    ok, err = await service.process_webhook(
        provider=PaymentProvider.YOOKASSA,
        raw_payload=payload,
        payload_bytes=body,
        signature=signature,
        headers=headers or {},
    )
    if err:
        return 400, err
    return 200, "OK"


async def process_cryptobot_webhook(
    service: PaymentService,
    body: bytes,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Process Crypto Pay webhook."""
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON: %s", e)
        return 400, "Invalid JSON"
    ok, err = await service.process_webhook(
        provider=PaymentProvider.CRYPTOBOT,
        raw_payload=payload,
        payload_bytes=body,
        headers=headers or {},
    )
    if err:
        return 400, err
    return 200, "OK"


async def process_telegram_stars_payment(
    service: PaymentService,
    payload: dict[str, Any],
) -> tuple[bool, str | None]:
    """
    Process Telegram successful_payment (from message handler).

    payload: {"successful_payment": {...}, "from": {"id": user_id}} or
             {"successful_payment": {...}, "user_id": user_id}
    """
    return await service.process_webhook(
        provider=PaymentProvider.TELEGRAM_STARS,
        raw_payload=payload,
    )
