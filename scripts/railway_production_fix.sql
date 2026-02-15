-- CRITICAL PRODUCTION FIX — Run in Railway PostgreSQL → Query
-- NO DROPS. NO DATA LOSS.

-- 1️⃣ FIX users.id autoincrement (if column has no sequence)
-- Run these one by one if DO block fails:
-- CREATE SEQUENCE IF NOT EXISTS users_id_seq;
-- ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
-- SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'users_id_seq') THEN
    CREATE SEQUENCE IF NOT EXISTS users_id_seq;
    ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
    PERFORM setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));
  END IF;
END $$;

-- 2️⃣ ADD missing tariff column in payments
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS tariff VARCHAR(50) NOT NULL DEFAULT '1_month';

-- 3️⃣ Ensure created_at exists in payments
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
