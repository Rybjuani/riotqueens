-- C3 / ADR 0008: RiotQueens owns the durable user UUID; Auth0 is an external binding.
-- Column names match apps/api/app/domain/identity.py (provider_subject, user_id).
-- Apply (upgrade):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f ops/migrations/0001_identity.sql
-- Downgrade is at the bottom (commented application notes).

BEGIN;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS external_identities (
  id BIGSERIAL PRIMARY KEY,
  provider TEXT NOT NULL,
  provider_subject TEXT NOT NULL,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (provider, provider_subject)
);

CREATE INDEX IF NOT EXISTS external_identities_user_id_idx
  ON external_identities (user_id);

COMMIT;

-- ---------------------------------------------------------------------------
-- Downgrade (run manually when rolling back C3 identity only):
--
-- BEGIN;
-- DROP INDEX IF EXISTS external_identities_user_id_idx;
-- DROP TABLE IF EXISTS external_identities;
-- DROP TABLE IF EXISTS users;
-- COMMIT;
-- ---------------------------------------------------------------------------
