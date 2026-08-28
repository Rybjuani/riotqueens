-- Append-only clickwrap acceptances (ADR 0004).
-- Linked to durable RiotQueens users.id (UUID). Auth0 sub never appears here.
-- Apply:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f ops/migrations/0003_clickwrap_acceptances.sql

BEGIN;

CREATE TABLE IF NOT EXISTS consent_acceptances (
  acceptance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  age_confirmed BOOLEAN NOT NULL,
  age_gate_version TEXT NOT NULL,
  terms_version TEXT NOT NULL,
  privacy_version TEXT NOT NULL,
  document_digest TEXT NOT NULL,
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS consent_acceptances_user_accepted_idx
  ON consent_acceptances (user_id, accepted_at DESC);

COMMIT;

-- ---------------------------------------------------------------------------
-- Downgrade:
-- BEGIN;
-- DROP INDEX IF EXISTS consent_acceptances_user_accepted_idx;
-- DROP TABLE IF EXISTS consent_acceptances;
-- COMMIT;
-- ---------------------------------------------------------------------------
