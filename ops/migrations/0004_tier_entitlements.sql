-- Server-owned product tier entitlements.
-- Auth0 authenticates; it never grants a RiotQueens tier by itself.
-- T0 is the implicit free/preview default when no active entitlement exists.

BEGIN;

CREATE TABLE IF NOT EXISTS user_tier_entitlements (
  entitlement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  tier SMALLINT NOT NULL CHECK (tier BETWEEN 1 AND 3),
  source TEXT NOT NULL,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  CHECK (expires_at IS NULL OR expires_at > granted_at)
);

CREATE INDEX IF NOT EXISTS user_tier_entitlements_user_granted_idx
  ON user_tier_entitlements (user_id, granted_at DESC);

COMMIT;
