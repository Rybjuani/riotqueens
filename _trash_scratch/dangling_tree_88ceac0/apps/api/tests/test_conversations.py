"""Unit tests for the conversation store.

Covers scope isolation, bounded history (pair-aware truncation), the
rollback helper, and basic concurrency ordering.

All tests are deterministic and do NOT call any paid model. The
InProcessConversationStore is exercised directly.
"""

from __future__ import annotations

import asyncio

import pytest

from app.domain.conversations import (
    ConversationScopeKey,
    InProcessConversationStore,
    _bound_pairs,
)


def _scope(
    user: str = "user-1",
    character: str = "queen-a",
    conv: str = "conv-1",
) -> ConversationScopeKey:
    return ConversationScopeKey(user_id=user, character_id=character, conversation_id=conv)


@pytest.mark.asyncio
async def test_first_message_history_is_empty() -> None:
    store = InProcessConversationStore(max_turns=8)
    history = await store.get_history(_scope())
    assert history == []


@pytest.mark.asyncio
async def test_append_user_then_assistant_yields_pair() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "hola")
    await store.append_assistant_message(scope, "hola, ¿qué tal?")
    history = await store.get_history(scope)
    assert [m.role for m in history] == ["user", "assistant"]
    assert [m.content for m in history] == ["hola", "hola, ¿qué tal?"]


@pytest.mark.asyncio
async def test_two_pairs_preserved_in_order() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    await store.append_assistant_message(scope, "a1")
    await store.append_user_message(scope, "u2")
    await store.append_assistant_message(scope, "a2")
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1", "a1", "u2", "a2"]


@pytest.mark.asyncio
async def test_trailing_user_preserved_when_pair_in_flight() -> None:
    """If a user message has no paired assistant yet (in-flight request),
    the trailing user turn is still preserved so the current request
    can be sent.
    """
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    await store.append_assistant_message(scope, "a1")
    await store.append_user_message(scope, "u2")  # in flight, no assistant
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1", "a1", "u2"]


@pytest.mark.asyncio
async def test_bounded_history_keeps_recent_complete_pairs() -> None:
    """With max_turns=2, only the last 2 complete pairs are kept."""
    store = InProcessConversationStore(max_turns=2)
    scope = _scope()
    for i in range(5):
        await store.append_user_message(scope, f"u{i}")
        await store.append_assistant_message(scope, f"a{i}")
    history = await store.get_history(scope)
    # Only pairs 3 and 4 survive.
    assert [m.content for m in history] == ["u3", "a3", "u4", "a4"]


@pytest.mark.asyncio
async def test_bounded_history_never_leaves_half_pair() -> None:
    """When truncating, the kept window always starts with a user message
    and ends with an assistant message (a complete pair), plus an
    optional trailing unpaired user turn.
    """
    store = InProcessConversationStore(max_turns=1)
    scope = _scope()
    for i in range(3):
        await store.append_user_message(scope, f"u{i}")
        await store.append_assistant_message(scope, f"a{i}")
    # Trailing in-flight user turn
    await store.append_user_message(scope, "u3-in-flight")
    history = await store.get_history(scope)
    # max_turns=1 → keep last complete pair (u2, a2) + trailing user.
    assert [m.content for m in history] == ["u2", "a2", "u3-in-flight"]


@pytest.mark.asyncio
async def test_max_turns_zero_still_keeps_trailing_user() -> None:
    """max_turns=0 still preserves the trailing in-flight user turn
    so the current request can be sent (Issue #5: "first message
    stores user turn, sends [system, user]").
    """
    store = InProcessConversationStore(max_turns=0)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1"]


@pytest.mark.asyncio
async def test_bounded_pairs_helper_directly() -> None:
    """Direct unit test for the _bound_pairs helper."""
    from app.domain.conversations import StoredMessage

    msgs = [
        StoredMessage(id="1", role="user", content="u1"),
        StoredMessage(id="2", role="assistant", content="a1"),
        StoredMessage(id="3", role="user", content="u2"),
        StoredMessage(id="4", role="assistant", content="a2"),
        StoredMessage(id="5", role="user", content="u3"),
        StoredMessage(id="6", role="assistant", content="a3"),
    ]
    out = _bound_pairs(msgs, max_turns=2)
    assert [m.content for m in out] == ["u2", "a2", "u3", "a3"]


@pytest.mark.asyncio
async def test_pop_last_user_message_if_match_rolls_back() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    await store.append_assistant_message(scope, "a1")
    await store.append_user_message(scope, "u2-failed")
    # Roll back the failed user message
    popped = await store.pop_last_user_message_if_match(scope, "u2-failed")
    assert popped is True
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1", "a1"]


@pytest.mark.asyncio
async def test_pop_last_user_message_no_match_does_nothing() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    await store.append_assistant_message(scope, "a1")
    # Try to pop a user message with different content — should NOT pop.
    popped = await store.pop_last_user_message_if_match(scope, "different-content")
    assert popped is False
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1", "a1"]


@pytest.mark.asyncio
async def test_pop_when_last_is_assistant_does_nothing() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope = _scope()
    await store.append_user_message(scope, "u1")
    await store.append_assistant_message(scope, "a1")
    popped = await store.pop_last_user_message_if_match(scope, "u1")
    assert popped is False
    history = await store.get_history(scope)
    assert [m.content for m in history] == ["u1", "a1"]


@pytest.mark.asyncio
async def test_delete_conversation_clears_only_that_scope() -> None:
    store = InProcessConversationStore(max_turns=8)
    scope_a = _scope(conv="conv-a")
    scope_b = _scope(conv="conv-b")
    await store.append_user_message(scope_a, "u-a")
    await store.append_assistant_message(scope_a, "a-a")
    await store.append_user_message(scope_b, "u-b")
    await store.append_assistant_message(scope_b, "a-b")
    deleted = await store.delete_conversation(scope_a)
    assert deleted is True
    # scope_b is untouched
    history_b = await store.get_history(scope_b)
    assert [m.content for m in history_b] == ["u-b", "a-b"]
    # scope_a is gone
    history_a = await store.get_history(scope_a)
    assert history_a == []


@pytest.mark.asyncio
async def test_delete_unknown_conversation_returns_false() -> None:
    store = InProcessConversationStore(max_turns=8)
    deleted = await store.delete_conversation(_scope(conv="never-existed"))
    assert deleted is False


@pytest.mark.asyncio
async def test_concurrent_appends_preserve_order() -> None:
    """Concurrent appends to the SAME scope must serialize so the
    final order is deterministic (Issue #5 task 10 / N).
    """
    store = InProcessConversationStore(max_turns=100)
    scope = _scope()

    # Fire 20 user+assistant pairs concurrently. The store's per-scope
    # asyncio.Lock must serialize the appends so no pair gets crossed.
    async def append_pair(i: int) -> None:
        await store.append_user_message(scope, f"u{i}")
        await store.append_assistant_message(scope, f"a{i}")

    await asyncio.gather(*(append_pair(i) for i in range(20)))
    history = await store.get_history(scope)
    # 20 pairs = 40 messages, all kept (max_turns=100).
    assert len(history) == 40
    # Verify pair integrity: every even index is user, every odd is
    # assistant, AND every user is followed by its matching assistant.
    for i in range(0, 40, 2):
        assert history[i].role == "user"
        assert history[i + 1].role == "assistant"
        # The user content prefix must match the assistant's.
        user_idx = int(history[i].content[1:])
        asst_idx = int(history[i + 1].content[1:])
        assert user_idx == asst_idx


@pytest.mark.asyncio
async def test_concurrent_appends_to_different_scopes_no_blocking() -> None:
    """Different scopes use different locks, so they should not block
    each other. This is mostly a smoke test — the goal is to verify
    no exception is raised and each scope ends up with its own state.
    """
    store = InProcessConversationStore(max_turns=10)
    scopes = [_scope(conv=f"conv-{i}") for i in range(5)]

    async def fill(scope: ConversationScopeKey, n: int) -> None:
        for i in range(n):
            await store.append_user_message(scope, f"u{i}")
            await store.append_assistant_message(scope, f"a{i}")

    await asyncio.gather(*(fill(s, 3) for s in scopes))
    for s in scopes:
        history = await store.get_history(s)
        assert len(history) == 6
