"""Auto-add missing columns to existing tables. Call from init_db when adding new columns."""

import logging
import re
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Whitelist of allowed table and column names (alphanumeric + underscore)
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_identifier(name: str) -> str:
    """Validate SQL identifier against whitelist pattern to prevent injection."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


async def ensure_column(engine, table: str, column_def: str) -> None:
    """
    Add column if it does not exist. PostgreSQL only.
    column_def example: "timezone VARCHAR(64) DEFAULT 'UTC'"

    All identifiers are validated against a strict whitelist pattern.
    """
    table = _validate_identifier(table)
    parts = column_def.strip().split()
    column_name = _validate_identifier(parts[0]) if parts else ""
    if not column_name:
        return

    # Use IF NOT EXISTS syntax (PostgreSQL 9.6+) — no dynamic SQL needed
    sql = text(
        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_def}"
    )
    async with engine.begin() as conn:
        try:
            await conn.execute(sql)
        except Exception as e:
            logger.warning("ensure_column %s.%s failed: %s", table, column_name, e)
