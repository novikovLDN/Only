"""
AdminAlertService — Telegram alerts with deduplication and recovery.
"""

import hashlib
import logging
from typing import TYPE_CHECKING

from app.config import settings
from app.config.constants import AlertSeverity
from app.models.admin_alert import AdminAlert
from app.models.base import get_async_session_maker
from app.repositories.admin_alert_repo import AdminAlertRepository

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

CRITICAL_COOLDOWN_MIN = 5
WARNING_COOLDOWN_MIN = 15


def _fingerprint(severity: str, source: str, message: str) -> str:
    """Deterministic hash for deduplication."""
    raw = f"{severity}:{source}:{message}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class AdminAlertService:
    """Send admin alerts with cooldown and recovery."""

    def __init__(self, bot: "Bot") -> None:
        self._bot = bot
        self._chat_id = settings.alert_chat_id_int

    def _cooldown_min(self, severity: AlertSeverity) -> int:
        return CRITICAL_COOLDOWN_MIN if severity == AlertSeverity.CRITICAL else WARNING_COOLDOWN_MIN

    async def send_alert(
        self,
        severity: AlertSeverity,
        source: str,
        message: str,
        fingerprint: str | None = None,
        details: dict | None = None,
    ) -> bool:
        """
        Send alert to admin. Deduplication by fingerprint + cooldown.
        Returns True if sent, False if skipped (cooldown).
        """
        if not self._chat_id:
            logger.warning("ALERT_CHAT_ID not set, skipping alert")
            return False
        fp = fingerprint or _fingerprint(severity.value, source, message)
        async with get_async_session_maker()() as session:
            repo = AdminAlertRepository(session)
            if await repo.was_alerted_recently(fp, self._cooldown_min(severity)):
                logger.debug("Alert skipped (cooldown): %s", fp)
                return False
            try:
                text = f"🚨 [{severity.value.upper()}] {source}\n{message}"
                await self._bot.send_message(chat_id=self._chat_id, text=text)
                alert = AdminAlert(
                    severity=severity.value,
                    source=source,
                    message=message[:500],
                    details=str(details)[:500] if details else None,
                    fingerprint=fp,
                )
                session.add(alert)
                await session.commit()
                return True
            except Exception as e:
                logger.exception("Failed to send alert: %s", e)
                await session.rollback()
                return False

    async def send_recovery(self, component: str, message: str) -> bool:
        """Send recovery notification."""
        if not self._chat_id:
            return False
        try:
            text = f"✅ [RECOVERED] {component}\n{message}"
            await self._bot.send_message(chat_id=self._chat_id, text=text)
            return True
        except Exception as e:
            logger.exception("Failed to send recovery: %s", e)
            return False
