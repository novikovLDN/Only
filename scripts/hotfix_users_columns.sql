-- HOTFIX: Add missing users columns (production-safe, zero-downtime)
-- Run in Railway PostgreSQL Query tab
-- NOTE: Use scripts/hotfix_schema_drift.sql for full schema sync.

ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) NOT NULL DEFAULT 'ru';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_until TIMESTAMPTZ NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_by_id BIGINT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) NOT NULL DEFAULT 'UTC';
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
