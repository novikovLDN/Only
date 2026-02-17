"""Auto-add missing columns to existing tables. Call from init_db when adding new columns."""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def ensure_column(engine, table: str, column_def: str) -> None:
    """
    Add column if it does not exist. PostgreSQL only.
    column_def example: "timezone VARCHAR(64) DEFAULT 'UTC'"
    """
    parts = column_def.strip().split()
    column_name = parts[0] if parts else ""
    if not column_name:
        return
    sql = text(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column_name}'
            ) THEN
                EXECUTE 'ALTER TABLE {table} ADD COLUMN {column_def}';
            END IF;
        END$$;
    """)
    async with engine.begin() as conn:
        try:
            await conn.execute(text(sql))
        except Exception as e:
            logger.warning("ensure_column %s.%s failed: %s", table, column_name, e)
