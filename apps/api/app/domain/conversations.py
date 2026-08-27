"""Server-side conversation history store (in-process prototype).

This module owns the in-process conversation state for RiotQueens.
It is intentionally NOT a database; it is a prototype store suitable for
single-process FastAPI runtimes. The Protocol-based interface
(`ConversationStore`) is designed so a future PostgreSQL / Redis backend
can be swapped in without changing the chat handler or the router.

Hard scope rules (Issue #5 + auditor fix PR #6)
----------------------------------------------
1. A conversation is identified by the tuple
   ``(user_id, character_id, conversation_id)``. The store MUST NOT mix
   messages across different users, characters, or conversation ids.
2. The canonical Queen system prompt is NEVER stored here. It is prepended
   to every model request from `app/domain/queens.py` at request time.
3. Only validated assistant content actually returned to the user may be
   stored as an assistant turn. Provider failures (timeout, 429, 5xx,
   auth/config, connect, malformed, empty) MUST NOT append a fake turn.
4. History is bounded deterministically by `max_turns`
   (`RIOTQUEENS_CONVERSATION_MAX_TURNS`). The bound is applied to complete
   user/assistant pairs; truncation never leaves a half-pair. The bound
   is applied to the STORED RECORD itself (not just the provider context)
   so in-process state cannot grow without limit.
5. Concurrent requests MUST NOT corrupt ordering. The in-process
   implementation uses a REENTRANT `asyncio.Lock` per scope key. The
   chat handler acquires the lock for the WHOLE turn lifecycle via
   `transaction(scope)` so two concurrent requests to the same
   conversation serialize completely: append user → assemble context →
   provider call → append assistant (or rollback on failure). Different
   conversation scopes use different locks and never block each other.
6. Per-scope locks are NEVER deleted (even when the conversation is
   deleted) to avoid the old-waiter / new-lock race. The prototype may
   accumulate one lock per scope ever seen — acceptable for a
   single-process prototype; a future persistent backend would manage
   lock lifecycle differently.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

import asyncpg

from .contracts import MessageInput


def _utcnow() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------- #
# Reentrant async lock — allows the same task to acquire the per-scope
# lock multiple times (transaction wraps multiple store calls).
# ---------------------------------------------------------------------- #


class _ReentrantAsyncLock:
    """A reentrant `asyncio.Lock`. The same task can acquire it multiple
    times without deadlocking. Acquisition count is tracked per-task so
    a matching number of releases fully frees the lock.

    This is used so the chat handler can hold the per-scope "transaction"
    lock for the whole turn lifecycle (append user → provider call →
    append assistant) while the store's public methods also acquire the
    same lock for their individual mutations. The reentrant property
    means the inner acquisitions are no-ops (just depth increments).
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._owner: asyncio.Task[object] | None = None
        self._depth = 0

    async def acquire(self) -> None:
        task = asyncio.current_task()
        if self._owner is task:
            self._depth += 1
            return
        await self._lock.acquire()
        self._owner = task
        self._depth = 1

    def release(self) -> None:
        task = asyncio.current_task()
        if self._owner is not task:
            raise RuntimeError("release() called by a task that does not own the lock")
        self._depth -= 1
        if self._depth == 0:
            self._owner = None
            self._lock.release()

    async def __aenter__(self) -> _ReentrantAsyncLock:
        await self.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        self.release()

    @property
    def is_locked(self) -> bool:
        """Return True if the lock is currently held by any task."""
        return self._lock.locked()


@dataclass(frozen=True)
class ConversationScopeKey:
    """The triple that isolates one conversation from every other.

    Equality and hashing are based on the full tuple so the same
    ``(user_id, character_id, conversation_id)`` always maps to the same
    in-process entry. Different users / characters / conversation ids
    always map to different entries — there is no possibility of
    cross-scope mixing.
    """

    user_id: str
    character_id: str
    conversation_id: str


@dataclass
class StoredMessage:
    """A single persisted message in a conversation history.

    Only ``role`` values ``"user"`` and ``"assistant"`` are stored here.
    System prompts are never persisted — they are always re-prepended at
    request time from `queens.py`.
    """

    id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class ConversationRecord:
    """A full conversation snapshot, scoped by (user, character, conversation)."""

    user_id: str
    character_id: str
    conversation_id: str
    messages: list[StoredMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


class ConversationStore(Protocol):
    """Swappable conversation persistence interface.

    The in-process implementation lives below; a future PostgreSQL or
    Redis-backed implementation can replace it without touching the chat
    handler or the router.
    """

    def transaction(self, scope: ConversationScopeKey) -> AsyncIterator[object]: ...

    async def append_user_message(
        self, scope: ConversationScopeKey, content: str
    ) -> StoredMessage: ...

    async def append_assistant_message(
        self, scope: ConversationScopeKey, content: str
    ) -> StoredMessage: ...

    async def get_history(self, scope: ConversationScopeKey) -> list[StoredMessage]: ...

    async def get_conversation(self, scope: ConversationScopeKey) -> ConversationRecord | None: ...

    async def delete_conversation(self, scope: ConversationScopeKey) -> bool: ...

    async def pop_last_user_message_if_match(
        self, scope: ConversationScopeKey, content: str
    ) -> bool: ...


def _split_pairs(
    messages: Sequence[StoredMessage],
) -> tuple[list[tuple[StoredMessage, StoredMessage]], StoredMessage | None]:
    """Split a message list into complete (user, assistant) pairs + optional trailing user.

    Returns ``(pairs, trailing_user)`` where ``pairs`` is a list of
    complete user/assistant pairs (oldest first) and ``trailing_user``
    is the last message if it is an unpaired user turn (i.e. a request
    is in flight).
    """
    pairs: list[tuple[StoredMessage, StoredMessage]] = []
    trailing_user: StoredMessage | None = None
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.role == "user":
            if i + 1 < len(messages) and messages[i + 1].role == "assistant":
                pairs.append((msg, messages[i + 1]))
                i += 2
                continue
            trailing_user = msg
            i += 1
        else:
            # assistant without preceding user, or unknown role — skip.
            i += 1
    return pairs, trailing_user


def _bound_pairs(messages: Sequence[StoredMessage], max_turns: int) -> list[StoredMessage]:
    """Return the most recent ``max_turns`` complete user/assistant pairs.

    The bound is applied to PAIRS, not individual messages, so truncation
    never leaves a dangling user message without its assistant reply (or
    vice versa). If the history ends with a single user turn (because the
    assistant turn has not been appended yet, which happens during a
    request), that trailing user turn is preserved on top of the bounded
    pair window.

    Parameters
    ----------
    messages
        The full ordered history (oldest first). Only ``"user"`` and
        ``"assistant"`` roles are expected here.
    max_turns
        Maximum number of complete user/assistant pairs to keep. Must be
        ``>= 0``. ``0`` means "no pairs returned" (the trailing unpaired
        user turn, if any, is still preserved so the current request can
        be sent).
    """
    if max_turns < 0:
        raise ValueError("max_turns must be >= 0")
    if not messages:
        return []
    pairs, trailing_user = _split_pairs(messages)
    if max_turns == 0:
        kept_pairs: list[tuple[StoredMessage, StoredMessage]] = []
    else:
        kept_pairs = pairs[-max_turns:]
    out: list[StoredMessage] = []
    for u, a in kept_pairs:
        out.append(u)
        out.append(a)
    if trailing_user is not None:
        out.append(trailing_user)
    return out


def _prune_record(record: ConversationRecord, max_turns: int) -> None:
    """Mutate ``record.messages`` in place to keep only the bounded set.

    After a successful assistant turn (or after a rollback), this is
    called to ensure the STORED record itself does not grow without
    limit. Keeps at most ``max_turns`` complete user/assistant pairs
    plus an optional trailing in-flight user message.
    """
    if max_turns < 0:
        return
    bounded = _bound_pairs(record.messages, max_turns)
    # Only mutate if we actually reduced the list (avoid unnecessary
    # list rebuilds on every turn when under the bound).
    if len(bounded) < len(record.messages):
        record.messages = bounded
        record.updated_at = _utcnow()


class InProcessConversationStore:
    """In-process implementation of `ConversationStore`.

    Holds conversation state in a plain dict keyed by `ConversationScopeKey`.
    Suitable for a single-process FastAPI deployment. Server restart
    clears all state — this is intentionally honest: it is NOT durable
    persistence.

    Concurrency (auditor fix PR #6):
        Each scope key has its own REENTRANT `_ReentrantAsyncLock`. The
        chat handler acquires the lock for the WHOLE turn lifecycle via
        ``async with store.transaction(scope):``. Two concurrent requests
        to the same conversation serialize completely — their
        append/context/provider/append mutations cannot interleave.
        Different conversation scopes use different locks and run in
        parallel. A slow provider in one conversation does NOT block
        other conversations.

        The lock is reentrant so the public methods (`append_user_message`,
        `get_history`, etc.) can also acquire the same lock for their
        individual mutations — if the caller already holds the
        transaction lock, the inner acquisition is a no-op.

        Per-scope locks are NEVER deleted (even when the conversation is
        deleted) to avoid the old-waiter / new-lock race. The prototype
        may accumulate one lock per scope ever seen (~100 bytes each);
        acceptable for a single-process prototype.
    """

    def __init__(self, max_turns: int = 8) -> None:
        if max_turns < 0:
            raise ValueError("max_turns must be >= 0")
        self._max_turns = max_turns
        self._records: dict[ConversationScopeKey, ConversationRecord] = {}
        self._locks: dict[ConversationScopeKey, _ReentrantAsyncLock] = {}

    def _lock_for(self, scope: ConversationScopeKey) -> _ReentrantAsyncLock:
        # Lazily create one reentrant lock per scope. Dict access is
        # atomic under the GIL for a single event loop.
        #
        # IMPORTANT (auditor fix): we NEVER delete per-scope locks, even
        # when the conversation is deleted. Deleting the lock while a
        # waiter holds it would let a new request create a second lock
        # and bypass the wait — a race. Keeping the lock around costs
        # ~100 bytes per scope ever seen, acceptable for a prototype.
        lock = self._locks.get(scope)
        if lock is None:
            lock = _ReentrantAsyncLock()
            self._locks[scope] = lock
        return lock

    def _record_for(self, scope: ConversationScopeKey) -> ConversationRecord:
        rec = self._records.get(scope)
        if rec is None:
            rec = ConversationRecord(
                user_id=scope.user_id,
                character_id=scope.character_id,
                conversation_id=scope.conversation_id,
            )
            self._records[scope] = rec
        return rec

    @property
    def max_turns(self) -> int:
        return self._max_turns

    @asynccontextmanager
    async def transaction(self, scope: ConversationScopeKey) -> AsyncIterator[None]:
        """Acquire the per-scope turn lock for the full chat turn lifecycle.

        The chat handler wraps its whole turn in this:

            async with conversation_store.transaction(scope):
                await conversation_store.append_user_message(scope, message)
                messages = await assemble_request_messages(...)
                response = await router.generate(request)
                await conversation_store.append_assistant_message(scope, response.content)
                # OR on any post-append failure or cancellation:
                await conversation_store.pop_last_user_message_if_match(scope, message)

        The lock is REENTRANT so the public methods called inside the
        transaction can re-acquire the same lock without deadlocking.

        Different conversation scopes use different locks and run in
        parallel. A slow provider in one conversation does NOT block
        other conversations.
        """
        async with self._lock_for(scope):
            yield

    async def append_user_message(self, scope: ConversationScopeKey, content: str) -> StoredMessage:
        async with self._lock_for(scope):
            rec = self._record_for(scope)
            msg = StoredMessage(id=str(uuid.uuid4()), role="user", content=content)
            rec.messages.append(msg)
            rec.updated_at = _utcnow()
            return msg

    async def append_assistant_message(
        self, scope: ConversationScopeKey, content: str
    ) -> StoredMessage:
        async with self._lock_for(scope):
            rec = self._record_for(scope)
            msg = StoredMessage(id=str(uuid.uuid4()), role="assistant", content=content)
            rec.messages.append(msg)
            # Prune the STORED record to the bound so in-process state
            # does not grow without limit (auditor fix PR #6 blocker 2).
            _prune_record(rec, self._max_turns)
            rec.updated_at = _utcnow()
            return msg

    async def get_history(self, scope: ConversationScopeKey) -> list[StoredMessage]:
        """Return the bounded history for a scope.

        The returned list contains at most ``max_turns`` complete
        user/assistant pairs, plus an optional trailing unpaired user
        message if a request is currently in flight. The canonical
        system prompt is NEVER included here — it is re-prepended at
        request time by `assemble_request` in `context.py`.

        Note: the stored record itself is also pruned to the bound after
        each successful assistant turn, so this method returns the same
        bounded view that the store actually holds. The bound is applied
        here too for defensive consistency (in case the record was
        mutated by a future code path that forgot to prune).
        """
        async with self._lock_for(scope):
            rec = self._records.get(scope)
            if rec is None:
                return []
            snapshot = list(rec.messages)
        return _bound_pairs(snapshot, self._max_turns)

    async def get_conversation(self, scope: ConversationScopeKey) -> ConversationRecord | None:
        """Return a deep-copy snapshot of the stored conversation record.

        The returned ``messages`` list reflects the BOUNDED stored state
        (the store prunes after each successful assistant turn). It does
        NOT contain messages beyond ``max_turns`` complete pairs (plus
        an optional in-flight trailing user). This is honest: the
        prototype does not keep full permanent history.
        """
        async with self._lock_for(scope):
            rec = self._records.get(scope)
            if rec is None:
                return None
            # Return a deep copy with the bounded view.
            bounded = _bound_pairs(rec.messages, self._max_turns)
            return ConversationRecord(
                user_id=rec.user_id,
                character_id=rec.character_id,
                conversation_id=rec.conversation_id,
                messages=bounded,
                created_at=rec.created_at,
                updated_at=rec.updated_at,
            )

    async def delete_conversation(self, scope: ConversationScopeKey) -> bool:
        """Delete a conversation by scope.

        Returns True if a conversation existed and was deleted, False if
        there was nothing to delete. Other conversations (different user /
        character / conversation_id) are NOT touched.

        Note (auditor fix): the per-scope lock is NOT deleted. It stays
        in ``self._locks`` so a waiter that was blocked on it when the
        delete happened still wakes up holding the SAME lock object (not
        a freshly-created one). A subsequent request to the same scope
        reuses the same lock, preserving serialization. The prototype may
        accumulate one lock per scope ever seen.
        """
        async with self._lock_for(scope):
            existed = scope in self._records
            if existed:
                del self._records[scope]
            return existed

    async def pop_last_user_message_if_match(
        self, scope: ConversationScopeKey, content: str
    ) -> bool:
        """Rollback helper for provider-failure state integrity (Issue #5).

        If the last stored message in this scope is a ``user`` message
        with the given ``content``, remove it and return True. Otherwise
        return False and leave the history untouched.

        This is used by the chat handler whenever context assembly,
        request construction, provider execution or assistant storage
        fails after the user append. The user message is popped so
        history is left in the state it was BEFORE the failed request.
        A subsequent retry can then produce a complete pair without a
        leftover failed half-turn.

        After the pop, the stored record is re-pruned to the bound
        defensively (though it should already be bounded from the
        previous successful turn).
        """
        async with self._lock_for(scope):
            rec = self._records.get(scope)
            if rec is None or not rec.messages:
                return False
            last = rec.messages[-1]
            if last.role == "user" and last.content == content:
                rec.messages.pop()
                _prune_record(rec, self._max_turns)
                rec.updated_at = _utcnow()
                return True
            return False

    # ------------------------------------------------------------------ #
    # Test-only inspection helpers (NOT part of the Protocol; used by
    # tests to verify the underlying stored state directly).
    # ------------------------------------------------------------------ #

    async def _raw_record(self, scope: ConversationScopeKey) -> ConversationRecord | None:
        """Return the RAW (unbounded) stored record for testing.

        Tests use this to verify that the stored state itself is pruned
        to the bound, not just the provider context. The returned object
        is a deep copy so tests cannot mutate internal state.
        """
        async with self._lock_for(scope):
            rec = self._records.get(scope)
            if rec is None:
                return None
            return ConversationRecord(
                user_id=rec.user_id,
                character_id=rec.character_id,
                conversation_id=rec.conversation_id,
                messages=list(rec.messages),
                created_at=rec.created_at,
                updated_at=rec.updated_at,
            )


def stored_to_message_input(msg: StoredMessage) -> MessageInput:
    """Convert a `StoredMessage` to a `MessageInput` for the provider request.

    Only ``"user"`` and ``"assistant"`` roles are stored, so this is always
    safe. The MessageInput contract enforces the same role pattern.
    """
    return MessageInput(role=msg.role, content=msg.content)


class PostgresConversationStore:
    """PostgreSQL-backed `ConversationStore` with in-process turn locks.

    Durability lives in Postgres. Same-process concurrency still uses the
    reentrant per-scope lock so a single API worker serializes a turn the
    same way as the in-process prototype. Multi-replica locking is a later
    hardening step (advisory locks), not required for the current single-API
    preprod layout.
    """

    def __init__(self, pool: asyncpg.Pool, max_turns: int = 8) -> None:
        if max_turns < 0:
            raise ValueError("max_turns must be >= 0")
        self._pool = pool
        self._max_turns = max_turns
        self._locks: dict[ConversationScopeKey, _ReentrantAsyncLock] = {}

    def _lock_for(self, scope: ConversationScopeKey) -> _ReentrantAsyncLock:
        lock = self._locks.get(scope)
        if lock is None:
            lock = _ReentrantAsyncLock()
            self._locks[scope] = lock
        return lock

    @property
    def max_turns(self) -> int:
        return self._max_turns

    @asynccontextmanager
    async def transaction(self, scope: ConversationScopeKey) -> AsyncIterator[None]:
        async with self._lock_for(scope):
            yield

    async def _ensure_conversation(
        self, connection: asyncpg.Connection, scope: ConversationScopeKey
    ) -> None:
        await connection.execute(
            """
            INSERT INTO conversations (user_id, character_id, conversation_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, character_id, conversation_id) DO NOTHING
            """,
            scope.user_id,
            scope.character_id,
            scope.conversation_id,
        )

    async def _load_messages(
        self, connection: asyncpg.Connection, scope: ConversationScopeKey
    ) -> list[StoredMessage]:
        rows = await connection.fetch(
            """
            SELECT id, role, content, created_at
            FROM conversation_messages
            WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
            ORDER BY created_at ASC, id ASC
            """,
            scope.user_id,
            scope.character_id,
            scope.conversation_id,
        )
        return [
            StoredMessage(
                id=str(row["id"]),
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def _touch(
        self, connection: asyncpg.Connection, scope: ConversationScopeKey
    ) -> None:
        await connection.execute(
            """
            UPDATE conversations
            SET updated_at = NOW()
            WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
            """,
            scope.user_id,
            scope.character_id,
            scope.conversation_id,
        )

    async def _prune(
        self, connection: asyncpg.Connection, scope: ConversationScopeKey
    ) -> None:
        messages = await self._load_messages(connection, scope)
        bounded = _bound_pairs(messages, self._max_turns)
        if len(bounded) >= len(messages):
            return
        keep_ids = [msg.id for msg in bounded]
        await connection.execute(
            """
            DELETE FROM conversation_messages
            WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
              AND NOT (id = ANY($4::uuid[]))
            """,
            scope.user_id,
            scope.character_id,
            scope.conversation_id,
            keep_ids,
        )

    async def append_user_message(
        self, scope: ConversationScopeKey, content: str
    ) -> StoredMessage:
        async with self._lock_for(scope):
            msg_id = uuid.uuid4()
            created_at = _utcnow()
            async with self._pool.acquire() as connection, connection.transaction():
                await self._ensure_conversation(connection, scope)
                await connection.execute(
                    """
                    INSERT INTO conversation_messages (
                      id, user_id, character_id, conversation_id, role, content, created_at
                    ) VALUES ($1, $2, $3, $4, 'user', $5, $6)
                    """,
                    msg_id,
                    scope.user_id,
                    scope.character_id,
                    scope.conversation_id,
                    content,
                    created_at,
                )
                await self._touch(connection, scope)
            return StoredMessage(
                id=str(msg_id), role="user", content=content, created_at=created_at
            )

    async def append_assistant_message(
        self, scope: ConversationScopeKey, content: str
    ) -> StoredMessage:
        async with self._lock_for(scope):
            msg_id = uuid.uuid4()
            created_at = _utcnow()
            async with self._pool.acquire() as connection, connection.transaction():
                await self._ensure_conversation(connection, scope)
                await connection.execute(
                    """
                    INSERT INTO conversation_messages (
                      id, user_id, character_id, conversation_id, role, content, created_at
                    ) VALUES ($1, $2, $3, $4, 'assistant', $5, $6)
                    """,
                    msg_id,
                    scope.user_id,
                    scope.character_id,
                    scope.conversation_id,
                    content,
                    created_at,
                )
                await self._prune(connection, scope)
                await self._touch(connection, scope)
            return StoredMessage(
                id=str(msg_id),
                role="assistant",
                content=content,
                created_at=created_at,
            )

    async def get_history(self, scope: ConversationScopeKey) -> list[StoredMessage]:
        async with self._lock_for(scope):
            async with self._pool.acquire() as connection:
                messages = await self._load_messages(connection, scope)
            return _bound_pairs(messages, self._max_turns)

    async def get_conversation(
        self, scope: ConversationScopeKey
    ) -> ConversationRecord | None:
        async with self._lock_for(scope):
            async with self._pool.acquire() as connection:
                meta = await connection.fetchrow(
                    """
                    SELECT created_at, updated_at
                    FROM conversations
                    WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
                    """,
                    scope.user_id,
                    scope.character_id,
                    scope.conversation_id,
                )
                if meta is None:
                    return None
                messages = await self._load_messages(connection, scope)
            return ConversationRecord(
                user_id=scope.user_id,
                character_id=scope.character_id,
                conversation_id=scope.conversation_id,
                messages=_bound_pairs(messages, self._max_turns),
                created_at=meta["created_at"],
                updated_at=meta["updated_at"],
            )

    async def delete_conversation(self, scope: ConversationScopeKey) -> bool:
        async with self._lock_for(scope):
            async with self._pool.acquire() as connection, connection.transaction():
                result = await connection.execute(
                    """
                    DELETE FROM conversations
                    WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
                    """,
                    scope.user_id,
                    scope.character_id,
                    scope.conversation_id,
                )
            # asyncpg status: "DELETE N"
            return result.rsplit(" ", 1)[-1] != "0"

    async def pop_last_user_message_if_match(
        self, scope: ConversationScopeKey, content: str
    ) -> bool:
        async with self._lock_for(scope):
            async with self._pool.acquire() as connection, connection.transaction():
                row = await connection.fetchrow(
                    """
                    SELECT id, role, content
                    FROM conversation_messages
                    WHERE user_id = $1 AND character_id = $2 AND conversation_id = $3
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    scope.user_id,
                    scope.character_id,
                    scope.conversation_id,
                )
                if row is None or row["role"] != "user" or row["content"] != content:
                    return False
                await connection.execute(
                    "DELETE FROM conversation_messages WHERE id = $1",
                    row["id"],
                )
                await self._prune(connection, scope)
                await self._touch(connection, scope)
                return True


__all__ = [
    "ConversationRecord",
    "ConversationScopeKey",
    "ConversationStore",
    "InProcessConversationStore",
    "PostgresConversationStore",
    "StoredMessage",
    "stored_to_message_input",
]

