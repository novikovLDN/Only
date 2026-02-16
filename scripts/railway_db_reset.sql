-- FULL ALEMBIC RESET — Fix "Can't locate revision identified by '011'"
-- Run in Railway PostgreSQL → Query Console
--
-- ROOT CAUSE: alembic_version table still contains old revision (011)
-- but migration files 011-013 were deleted. Alembic cannot upgrade.
--
-- This script: DROP public schema (removes all tables + alembic_version)
-- After running: redeploy → alembic upgrade head will apply 014 from scratch

-- ⚠️ DATA LOSS: All tables and data will be deleted.

-- STEP 1 — Reset schema
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- STEP 2 — Verify (run separately; result should be empty)
-- SELECT * FROM information_schema.tables WHERE table_schema = 'public';
