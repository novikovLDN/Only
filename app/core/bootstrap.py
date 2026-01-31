"""
Startup bootstrap — migrations, single-instance lock, schema verification.

FAIL FAST: any step fails → abort startup, do not poll Telegram.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.config import settings
from app.models.base import get_async_session_maker

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = 6214188086


async def check_migrations_pending() -> bool:
    """
    Return True if migrations are pending (current != head).
    Must run alembic upgrade head before starting app.
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy.engine import Connection

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        if head is None:
            logger.warning("No alembic head found")
            return False

        session_factory = get_async_session_maker()
        async with session_factory() as session:
            def _get_current(conn: Connection) -> str | None:
                context = MigrationContext.configure(
                    conn, opts={"version_table": "alembic_version"}
                )
                return context.get_current_revision()

            conn = await session.connection()
            current = await conn.run_sync(_get_current)
            pending = current != head
            if pending:
                logger.critical(
                    "DATABASE SCHEMA OUT OF SYNC — ABORTING STARTUP. "
                    "Current: %s, Head: %s. Run: alembic upgrade head",
                    current,
                    head,
                )
            return pending
    except Exception as e:
        logger.exception("Migration check failed: %s", e)
        return True  # Assume pending on error — fail safe


async def verify_schema() -> bool:
    """
    Verify users table has required columns.
    Return False if schema mismatch.
    """
    required_columns = {"notifications_enabled", "profile_views_count"}
    try:
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'users'
                    """
                )
            )
            existing = {row[0] for row in result.fetchall()}
            missing = required_columns - existing
            if missing:
                logger.critical(
                    "DATABASE SCHEMA OUT OF SYNC — ABORTING STARTUP. "
                    "Missing columns in users: %s. Run: alembic upgrade head",
                    missing,
                )
                return False
            return True
    except Exception as e:
        logger.exception("Schema verification failed: %s", e)
        return False


def check_instance_role() -> bool:
    """
    If BOT_INSTANCE_ROLE is set, only 'primary' may run.
    Railway: set BOT_INSTANCE_ROLE=primary for single replica.
    """
    role = getattr(settings, "bot_instance_role", None) or ""
    if not role:
        return True
    if role.strip().lower() == "primary":
        return True
    logger.critical(
        "BOT_INSTANCE_ROLE=%s — not primary. Exiting.",
        role,
    )
    return False


async def bootstrap() -> bool:
    """
    Run all startup checks. Returns True if OK, False to abort.
    Order: role check → migrations → schema.
    """
    if not check_instance_role():
        return False

    if await check_migrations_pending():
        return False

    if not await verify_schema():
        return False

    logger.info("Bootstrap complete")
    return True
