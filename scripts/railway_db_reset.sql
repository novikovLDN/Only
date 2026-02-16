-- HARD RESET — Fix "Can't locate revision identified by '011'"
-- Run in Railway PostgreSQL → Query
-- This removes ALL tables and alembic_version. After this, run: alembic upgrade head

-- ⚠️ DATA LOSS: All data will be deleted. Use only for broken migration state.

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
