"""Admin audit logging service."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admin_audit_log import AdminAuditLog

logger = logging.getLogger(__name__)


async def log_admin_action(
    session: AsyncSession,
    admin_id: int,
    action: str,
    target_user_id: int | None = None,
    details: str | None = None,
) -> None:
    """Record an admin action in the audit log."""
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        details=details,
    )
    session.add(entry)
    await session.flush()
    logger.info("Admin audit: admin=%s action=%s target=%s", admin_id, action, target_user_id)
