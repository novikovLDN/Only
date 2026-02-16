-- DATABASE HARD RESET — Fix "Can't locate revision identified by '011'"
-- Run in Railway PostgreSQL → Query Console
--
-- ROOT CAUSE: alembic_version contains '011' but migration 011 was deleted.
-- Alembic cannot upgrade. Must reset DB to clean state.
--
-- ⚠️ DATA LOSS: All tables and data will be deleted.

-- STEP 1 — Reset schema (removes all tables + alembic_version)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- STEP 2 — Verify (run separately; result must be EMPTY)
-- SELECT * FROM information_schema.tables WHERE table_schema='public';

-- After this: redeploy app. Start command: alembic upgrade head && python -m app.main
-- Expected log: Running upgrade  -> 014_final_schema_rebuild
