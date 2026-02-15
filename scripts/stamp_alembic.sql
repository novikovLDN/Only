-- Stamp existing DB so Alembic does not try to recreate tables.
-- Run in Railway → PostgreSQL → Query when tables already exist but alembic_version is empty.
--
-- 1. If alembic_version does not exist:
-- CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
--
-- 2. If empty, stamp with revision 001 (matches alembic/versions/001_initial.py):
INSERT INTO alembic_version (version_num) VALUES ('001');
