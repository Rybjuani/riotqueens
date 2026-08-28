-- Durable conversation history and explicit user-fact memories.
-- Scopes mirror apps/api/app/domain/conversations.py and memories.py:
--   conversation: (user_id, character_id, conversation_id)
--   memory:       (user_id, character_id)
-- Apply:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f ops/migrations/0002_conversations_memories.sql

BEGIN;

CREATE TABLE IF NOT EXISTS conversations (
  user_id TEXT NOT NULL,
  character_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, character_id, conversation_id)
);

CREATE TABLE IF NOT EXISTS conversation_messages (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  character_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  FOREIGN KEY (user_id, character_id, conversation_id)
    REFERENCES conversations (user_id, character_id, conversation_id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS conversation_messages_scope_created_idx
  ON conversation_messages (user_id, character_id, conversation_id, created_at, id);

CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  character_id TEXT NOT NULL,
  content TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  source TEXT NOT NULL,
  confidence TEXT NOT NULL,
  inferred BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memories_scope_created_idx
  ON memories (user_id, character_id, created_at, id);

COMMIT;

-- ---------------------------------------------------------------------------
-- Downgrade:
-- BEGIN;
-- DROP INDEX IF EXISTS memories_scope_created_idx;
-- DROP TABLE IF EXISTS memories;
-- DROP INDEX IF EXISTS conversation_messages_scope_created_idx;
-- DROP TABLE IF EXISTS conversation_messages;
-- DROP TABLE IF EXISTS conversations;
-- COMMIT;
-- ---------------------------------------------------------------------------
