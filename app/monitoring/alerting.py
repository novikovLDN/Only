"""
Admin Telegram alerts with deduplication.
"""

import hashlib
from datetime import datetime, timedelta

from aiogram import Bot

from app.config import settings
from app.config.constants import AlertSeverity
from app.models.base import get_async_session_maker
from app.models.system_log import SystemLog
from app.repositories.system_log_repo import SystemLogRepository


CRITICAL_INTERVAL_MIN = 5
WARNING_INTERVAL_MIN = 15


async def send_alert(bot: Bot, severity: AlertSeverity, message: str, fingerprint: str | None = None) -> None:
    """
    Send alert to admin. Deduplicate: same fingerprint within interval = skip.
    """
    chat_id = settings.alert_chat_id_int
    if not chat_id:
        return
    fp = fingerprint or hashlib.sha256(message.encode()).hexdigest()[:32]
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        repo = SystemLogRepository(session)
        interval = CRITICAL_INTERVAL_MIN if severity == AlertSeverity.CRITICAL else WARNING_INTERVAL_MIN
        recent = await repo.get_recent_by_fingerprint(fp, since_minutes=interval)
        if recent:
            return  # Already alerted
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🚨 [{severity.value.upper()}]\n{message}",
            )
            log = SystemLog(
                severity=severity.value,
                source="alerting",
                message=message[:500],
                fingerprint=fp,
                alerted_at=datetime.utcnow().isoformat(),
            )
            await repo.add(log)
            await session.commit()
        except Exception:
            await session.rollback()
