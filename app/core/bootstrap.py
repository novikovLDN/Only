"""
Startup bootstrap — migrations, schema verification, instance role.

Migrations pending → ABORT (fail deploy).
Schema mismatch → DEGRADED (disable scheduler, allow bot with limited functionality).
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.config import settings
from app.models.base import get_async_session_maker
from app.core.runtime_state import set_schema_ok

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
    On mismatch: set degraded mode, DO NOT abort — allow bot with limited functionality.
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
                    "DATABASE SCHEMA OUT OF SYNC — DEGRADED MODE. "
                    "Missing columns in users: %s. Run: alembic upgrade head. "
                    "Scheduler disabled. Bot runs with limited functionality.",
                    missing,
                )
                set_schema_ok(False)
                return False
            set_schema_ok(True)
            return True
    except Exception as e:
        logger.exception("Schema verification failed: %s", e)
        set_schema_ok(False)
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


async def bootstrap() -> tuple[bool, bool]:
    """
    Run startup checks.
    Returns (proceed, schema_ok).
    - proceed=False → abort startup (migrations pending, instance role)
    - proceed=True, schema_ok=False → degraded mode (no scheduler)
    - proceed=True, schema_ok=True → full mode
    """
    if not check_instance_role():
        return False, False

    if await check_migrations_pending():
        return False, False

    schema_ok = await verify_schema()

    logger.info("Bootstrap complete (schema_ok=%s)", schema_ok)
    return True, schema_ok
