"""2328.io Crypto payment service."""

import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.premium import PREMIUM_TARIFFS
from app.models import Payment, Referral, User
from app.services.referral_service import give_reward_if_pending
from app.services.user_service import extend_premium

logger = logging.getLogger(__name__)

BASE_URL = "https://api.2328.io/api"
NETWORK = "TRX-TRC20"
CURRENCY = "USDT"


def _sign_body(body: dict, api_key: str) -> str:
    """HMAC-SHA256 sign: json -> base64 -> hmac."""
    payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    sig = hmac.new(
        api_key.encode("utf-8") if isinstance(api_key, str) else api_key,
        b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return sig


def verify_webhook_signature(data: dict, api_key: str) -> bool:
    """Verify webhook sign. Remove sign from data, compute HMAC, compare."""
    if not api_key or "sign" not in data:
        return False
    received = data.pop("sign", None)
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    expected = hmac.new(
        api_key.encode("utf-8"),
        b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received or "")


async def create_crypto_payment(
    session: AsyncSession,
    user: User,
    tariff_code: str,
    order_id: str,
    url_callback: str,
) -> tuple[Payment | None, str]:
    """
    Create crypto payment via 2328 API.
    Saves Payment (provider=crypto, status=check) and returns it.
    """
    if not settings.crypto_api_key:
        logger.error("CRYPTO_API_KEY not set")
        return None, ""

    tinfo = PREMIUM_TARIFFS.get(tariff_code) or PREMIUM_TARIFFS["1M"]
    months = tinfo["months"]
    price_usd = _rub_to_usd(tinfo["price_rub"])
    tariff_name = {1: "1m", 3: "3m", 6: "6m", 12: "12m"}.get(months, "1m")

    # Create pending payment in DB first
    payment = Payment(
        user_id=user.id,
        tariff=tariff_name,
        amount=int(tinfo["price_rub"] * 100),
        provider="crypto",
        status="pending",
        external_payment_id=None,
    )
    session.add(payment)
    await session.flush()
    await session.refresh(payment)

    body = {
        "amount": str(round(price_usd, 2)),
        "currency": "USD",
        "order_id": order_id,
        "to_currency": CURRENCY,
        "network": NETWORK,
        "url_callback": url_callback,
    }
    sign = _sign_body(body, settings.crypto_api_key)
    headers = {
        "Content-Type": "application/json",
        "project": settings.crypto_project_id,
        "sign": sign,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{BASE_URL}/v1/payment", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.exception("2328 create payment failed: %s", e)
        payment.status = "cancel"
        await session.flush()
        return None, ""

    result = data.get("result") or data
    ext_id = result.get("uuid")
    url = result.get("url", "")
    address = result.get("address", "")
    expires_str = result.get("expires_at")

    if not ext_id or not address:
        logger.error("2328 response missing uuid/address: %s", data)
        payment.status = "cancel"
        await session.flush()
        return None, ""

    pay_url = result.get("url", "")

    payment.external_payment_id = ext_id
    payment.crypto_network = NETWORK
    payment.crypto_currency = CURRENCY
    payment.crypto_address = address
    payment.status = "check"
    if expires_str:
        try:
            # ISO format
            payment.expires_at = datetime.fromisoformat(
                expires_str.replace("Z", "+00:00")
            )
        except Exception:
            pass
    await session.flush()
    return payment, pay_url


def _rub_to_usd(price_rub: float) -> float:
    """Approximate RUB->USD. Adjust or use live rate later."""
    return round(price_rub / 100, 2)


async def process_crypto_webhook(
    session: AsyncSession,
    data: dict,
    bot=None,
) -> tuple[int, str]:
    """
    Process 2328 webhook. Idempotent.
    Returns (status_code, body).
    """
    if not verify_webhook_signature(dict(data), settings.crypto_api_key):
        logger.warning("Crypto webhook invalid signature")
        return 401, ""

    ext_id = data.get("uuid") or data.get("external_payment_id")
    status = (data.get("payment_status") or data.get("status") or "").lower()

    if not ext_id:
        return 200, ""

    result = await session.execute(
        select(Payment).where(Payment.external_payment_id == ext_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        logger.warning("Crypto webhook unknown external_id=%s", ext_id)
        return 200, ""

    if payment.status in ("paid", "completed"):
        return 200, ""

    if status in ("paid", "overpaid"):
        payment.status = "paid"
        tariff_months = {"1m": 1, "3m": 3, "6m": 6, "12m": 12}
        months = tariff_months.get(payment.tariff, 1)
        user = await session.get(User, payment.user_id)
        if user:
            await extend_premium(session, user, months)
            referral = (
                await session.execute(
                    select(Referral).where(Referral.referral_user_id == user.id)
                )
            ).scalar_one_or_none()
            if referral:
                referrer = await give_reward_if_pending(session, referral)
                if referrer and bot:
                    try:
                        from app.texts import t
                        lang = referrer.language_code if referrer.language_code in ("ru", "en", "ar") else "ru"
                        await bot.send_message(
                            chat_id=referrer.telegram_id,
                            text=t(lang, "referral_bonus_notify"),
                        )
                    except Exception:
                        pass
            if bot:
                try:
                    from app.texts import t
                    from app.keyboards import main_menu
                    from app.services import user_service
                    lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=t(lang, "premium_success"),
                        reply_markup=main_menu(lang, user_service.is_premium(user)),
                    )
                except Exception as e:
                    logger.warning("Notify user premium failed: %s", e)
            from app.services import achievement_service
            try:
                await achievement_service.check_achievements(
                    session, user.id, user, bot, user.telegram_id, trigger="subscription_purchased"
                )
            except Exception:
                pass
        await session.flush()
    elif status == "underpaid":
        if bot and payment.user_id:
            user = await session.get(User, payment.user_id)
            if user:
                try:
                    from app.texts import t
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=t(user.language_code or "ru", "crypto_underpaid"),
                    )
                except Exception:
                    pass
        payment.status = "underpaid"
        await session.flush()
    elif status == "cancel":
        payment.status = "cancel"
        await session.flush()

    return 200, ""
