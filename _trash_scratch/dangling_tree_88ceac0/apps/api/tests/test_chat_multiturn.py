"""Integration tests for the multi-turn chat flow with conversation + memory.

These tests use a custom MockProvider that records the `ModelRequest` it
receives, so we can verify the canonical context assembly:

    system Bardera prompt
    → server-owned memory context (only if memories exist)
    → server-owned voice exemplars (few-shot style anchors)
    → bounded conversation history (prior user/assistant turns)
    → current user message

Covers Issue #5 acceptance cases A through O (a few are split across
test files — see test_conversations.py and test_memories.py for store
unit tests).
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

from app.domain.contracts import MessageInput, ModelRequest, ModelResponse, Route, Usage
from app.domain.providers.errors import ProviderContentBlockedError
from app.domain.queens import BARDERA_VOICE_EXEMPLARS
from app.domain.router import ModelRouter
from app.domain.validation import OutputValidator
from tests.asgi_test_client import SyncASGIClient as TestClient

# Server-owned few-shot pairs injected before live conversation history.
_VOICE_EXEMPLAR_COUNT = len(BARDERA_VOICE_EXEMPLARS)


def _live_messages(messages: list) -> list:
    """Strip system blocks + bracketed voice exemplars; return live tail."""

    # After optional leading system blocks, expect:
    # [style-open system] + N exemplars + [style-close system] + live...
    i = 0
    while i < len(messages) and messages[i].role == "system":
        # Stop at the style-open marker if present; otherwise pure system prefix.
        if "Anclas de estilo" in messages[i].content:
            break
        i += 1
    if (
        i < len(messages)
        and messages[i].role == "system"
        and "Anclas de estilo" in messages[i].content
    ):
        i += 1  # style-open
        i += _VOICE_EXEMPLAR_COUNT
        if i < len(messages) and messages[i].role == "system":
            i += 1  # style-close
        return messages[i:]
    # No exemplars path.
    return messages[i:]

# ---------------------------------------------------------------------- #
# Test fixtures — a capturing MockProvider + a fresh FastAPI app per test
# ---------------------------------------------------------------------- #


class CapturingMockProvider:
    """A MockModelProvider that records every ModelRequest it sees.

    Used to assert exactly which `messages` list the provider received,
    so we can verify the canonical context assembly order.
    """

    name = "capturing-mock"
    model = "capturing-mock-v1"

    def __init__(self, *, reply: str | None = None) -> None:
        # If `reply` is None, echo a deterministic Spanish reply per call.
        self._reply = reply
        self.captured_requests: list[ModelRequest] = []

    async def generate(self, request: ModelRequest) -> ModelResponse:
        # Make a defensive copy so later mutations of the request do not
        # retroactively change what we captured.
        self.captured_requests.append(
            ModelRequest(
                route=request.route,
                character_id=request.character_id,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                messages=[MessageInput(role=m.role, content=m.content) for m in request.messages],
                memories=list(request.memories),
                tools=list(request.tools),
                metadata=dict(request.metadata),
            )
        )
        if self._reply is not None:
            content = self._reply
        else:
            # Deterministic Spanish reply that passes OutputValidator.
            # Must include a Spanish marker word ("te", "hola", "de",
            # "la", "el", "me", "que", "con", "para", "una") so
            # `_looks_like_spanish` returns True. We use "Te leo. Esta
            # es mi respuesta número N." which has "te" as a marker.
            n = len(self.captured_requests)
            content = f"Te leo. Esta es mi respuesta número {n}."
        return ModelResponse(
            provider=self.name,
            model=self.model,
            content=content,
            usage=Usage(input_tokens=10, output_tokens=10),
        )


@pytest.fixture()
def fresh_app(monkeypatch: pytest.MonkeyPatch):
    """Force-reload app.main with a fresh CapturingMockProvider wired in.

    Each test gets a clean FastAPI app + clean in-process stores + a
    CapturingMockProvider so we can assert on the exact messages list
    the provider saw.
    """
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "mock")
    monkeypatch.setenv("RIOTQUEENS_CONVERSATION_MAX_TURNS", "8")
    monkeypatch.setenv("RIOTQUEENS_MEMORY_MAX_PER_SCOPE", "32")

    import app.main as main_mod

    importlib.reload(main_mod)

    # Replace the router's mock provider with our capturing one so we
    # can assert on the exact messages list. We swap every route to
    # the same capturing provider so any route works.
    capturing = CapturingMockProvider()
    new_router = ModelRouter(
        providers={route: capturing for route in Route},
        validator=OutputValidator(),
        timeout_seconds=5.0,
        max_retries=1,
    )
    main_mod.router = new_router

    client = TestClient(main_mod.app)
    return client, capturing, main_mod


# ---------------------------------------------------------------------- #
# A. First message: provider receives [system, user1]
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_A_first_message_provider_receives_system_and_user(fresh_app) -> None:
    client, capturing, _ = fresh_app
    resp = client.post(
        "/v1/chat",
        json={
            "message": "Hola Bardera, ¿cómo estás?",
            "character_id": "bardera",
            "user_id": "user-A",
            "conversation_id": "conv-A",
        },
    )
    assert resp.status_code == 200
    assert len(capturing.captured_requests) == 1
    request = capturing.captured_requests[0]
    assert request.route is Route.FAST_CHAT
    msgs = request.messages
    roles = [m.role for m in msgs]
    # system + voice exemplars (user/assistant pairs) + current user.
    assert roles[0] == "system"
    assert roles[-1] == "user"
    assert "Sos La Bardera" in msgs[0].content
    assert "tema identitario" in msgs[0].content.lower()
    assert "bardera lavada" in msgs[0].content.lower()
    # Style samples live inside the system prompt (no fake chat turns).
    assert "MUESTRAS DE VOZ" in msgs[0].content
    assert "Manaos" in msgs[0].content
    assert roles == ["system", "user"]
    assert msgs[-1].content == "Hola Bardera, ¿cómo estás?"


# ---------------------------------------------------------------------- #
# B. Second message: provider receives [system, user1, assistant1, user2]
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_B_second_message_provider_receives_prior_turn(fresh_app) -> None:
    client, capturing, _ = fresh_app
    # First message
    client.post(
        "/v1/chat",
        json={
            "message": "primer mensaje",
            "character_id": "bardera",
            "user_id": "user-B",
            "conversation_id": "conv-B",
        },
    )
    # Second message
    client.post(
        "/v1/chat",
        json={
            "message": "segundo mensaje",
            "character_id": "bardera",
            "user_id": "user-B",
            "conversation_id": "conv-B",
        },
    )
    assert len(capturing.captured_requests) == 2

    # First request live tail: [user1]
    live_1 = _live_messages(capturing.captured_requests[0].messages)
    assert [m.role for m in live_1] == ["user"]
    assert live_1[0].content == "primer mensaje"

    # Second request live tail: [user1, assistant1, user2]
    live_2 = _live_messages(capturing.captured_requests[1].messages)
    assert [m.role for m in live_2] == ["user", "assistant", "user"]
    assert live_2[0].content == "primer mensaje"
    assert live_2[1].content.startswith("Te leo. Esta es mi respuesta número 1")
    assert live_2[2].content == "segundo mensaje"


# ---------------------------------------------------------------------- #
# C. Different conversation_id → fully isolated
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_C_different_conversation_id_isolated(fresh_app) -> None:
    client, capturing, _ = fresh_app
    client.post(
        "/v1/chat",
        json={
            "message": "conv-1 msg",
            "character_id": "bardera",
            "user_id": "user-C",
            "conversation_id": "conv-C-1",
        },
    )
    client.post(
        "/v1/chat",
        json={
            "message": "conv-2 msg",
            "character_id": "bardera",
            "user_id": "user-C",
            "conversation_id": "conv-C-2",
        },
    )
    # The second request must NOT contain the first conversation's messages.
    live_2 = _live_messages(capturing.captured_requests[1].messages)
    assert [m.role for m in live_2] == ["user"]
    assert live_2[0].content == "conv-2 msg"


# ---------------------------------------------------------------------- #
# D. Different user_id → fully isolated
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_D_different_user_id_isolated(fresh_app) -> None:
    client, capturing, _ = fresh_app
    client.post(
        "/v1/chat",
        json={
            "message": "alice msg",
            "character_id": "bardera",
            "user_id": "alice",
            "conversation_id": "shared-conv",
        },
    )
    client.post(
        "/v1/chat",
        json={
            "message": "bob msg",
            "character_id": "bardera",
            "user_id": "bob",
            "conversation_id": "shared-conv",
        },
    )
    # Bob's request must NOT contain Alice's messages, even though the
    # conversation_id is the same string.
    msgs_2 = capturing.captured_requests[1].messages
    contents = [m.content for m in msgs_2]
    assert "alice msg" not in contents
    assert "bob msg" in contents


# ---------------------------------------------------------------------- #
# E. Unknown Queens are rejected before touching runtime state
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        (
            "POST",
            "/v1/chat",
            {
                "message": "unknown queen message",
                "character_id": "other-character",
                "user_id": "user-E",
                "conversation_id": "shared-conv",
            },
        ),
        (
            "GET",
            "/v1/conversations/shared-conv?user_id=user-E&character_id=other-character",
            None,
        ),
        (
            "DELETE",
            "/v1/conversations/shared-conv",
            {"user_id": "user-E", "character_id": "other-character"},
        ),
        (
            "GET",
            "/v1/memories?user_id=user-E&character_id=other-character",
            None,
        ),
        (
            "POST",
            "/v1/memories",
            {
                "user_id": "user-E",
                "character_id": "other-character",
                "content": "unknown queen memory",
            },
        ),
        (
            "DELETE",
            "/v1/memories/00000000-0000-0000-0000-000000000000",
            {"user_id": "user-E", "character_id": "other-character"},
        ),
    ],
)
async def test_E_unknown_queen_rejected_before_provider_or_store_access(
    fresh_app, method: str, path: str, payload: dict[str, str] | None
) -> None:
    client, capturing, main_mod = fresh_app

    resp = client.request(method, path, json=payload)

    assert resp.status_code == 404
    assert resp.json() == {
        "detail": {
            "code": "queen_not_found",
            "message": "Queen is not available.",
        }
    }
    assert capturing.captured_requests == []
    assert main_mod.conversation_store._records == {}
    assert main_mod.conversation_store._locks == {}
    assert main_mod.memory_store._records == {}
    assert main_mod.memory_store._locks == {}


@pytest.mark.asyncio
async def test_public_chat_route_cannot_be_selected_by_client(fresh_app) -> None:
    client, capturing, main_mod = fresh_app

    resp = client.post(
        "/v1/chat",
        json={
            "message": "try vision route",
            "character_id": "bardera",
            "user_id": "user-route",
            "conversation_id": "conversation-route",
            "route": "vision",
        },
    )

    assert resp.status_code == 422
    assert capturing.captured_requests == []
    assert main_mod.conversation_store._records == {}
    assert main_mod.conversation_store._locks == {}


# ---------------------------------------------------------------------- #
# F. Provider failure does NOT append a fake assistant turn / pollute history
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_F_provider_failure_does_not_pollute_history(fresh_app) -> None:
    """A provider failure must not append a fake assistant turn, and the
    failed user message must be rolled back so the next request starts
    clean.
    """
    client, capturing, main_mod = fresh_app

    # Replace the router with one whose provider always raises a
    # ProviderError on the FIRST call, then succeeds on subsequent calls.
    from app.domain.providers.errors import ProviderConnectError

    class FlakyProvider:
        name = "flaky"
        model = "flaky-v1"
        calls = 0

        async def generate(self, request: ModelRequest) -> ModelResponse:
            self.calls += 1
            if self.calls == 1:
                raise ProviderConnectError()
            # Recovery reply — must pass OutputValidator. "Te recupero."
            # has "te" as a Spanish marker word.
            return ModelResponse(
                provider=self.name,
                model=self.model,
                content="Te recupero. Volví a responder con normalidad.",
                usage=Usage(input_tokens=10, output_tokens=10),
            )

    flaky = FlakyProvider()
    main_mod.router = ModelRouter(
        providers={route: flaky for route in Route},
        validator=OutputValidator(),
        max_retries=0,  # don't retry — fail fast
    )

    # First call: provider fails → 503 (clean provider error).
    resp1 = client.post(
        "/v1/chat",
        json={
            "message": "primer mensaje que falla",
            "character_id": "bardera",
            "user_id": "user-F",
            "conversation_id": "conv-F",
        },
    )
    assert resp1.status_code == 503
    assert resp1.json()["detail"]["code"] == "provider_connect_failed"

    # Verify the failed user message was rolled back: GET the
    # conversation, it should be empty.
    convo = client.get("/v1/conversations/conv-F?user_id=user-F&character_id=bardera").json()
    assert convo["messages"] == []

    # Second call: succeeds. Provider should receive [system, user]
    # — NOT [system, user-failed, user2]. The rollback worked.
    resp2 = client.post(
        "/v1/chat",
        json={
            "message": "segundo mensaje después del fallo",
            "character_id": "bardera",
            "user_id": "user-F",
            "conversation_id": "conv-F",
        },
    )
    assert resp2.status_code == 200
    # The flaky provider's captured request: only the second call.
    assert flaky.calls == 2
    # We can't easily get the captured request from `flaky` since it
    # doesn't store them. But we CAN verify via the GET endpoint that
    # the conversation now has exactly [user2, assistant2] — no failed
    # turn lingering.
    convo_after = client.get("/v1/conversations/conv-F?user_id=user-F&character_id=bardera").json()
    msgs = convo_after["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "segundo mensaje después del fallo"
    assert msgs[1]["content"] == "Te recupero. Volví a responder con normalidad."


# ---------------------------------------------------------------------- #
# G. Bounded history: exceeds max_turns, keeps recent complete pairs
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_G_bounded_history_keeps_recent_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    """With RIOTQUEENS_CONVERSATION_MAX_TURNS=2, after sending 5 messages
    the provider should only receive the last 2 complete pairs + the
    current user message.
    """
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "mock")
    monkeypatch.setenv("RIOTQUEENS_CONVERSATION_MAX_TURNS", "2")
    monkeypatch.setenv("RIOTQUEENS_MEMORY_MAX_PER_SCOPE", "32")

    import app.main as main_mod

    importlib.reload(main_mod)
    capturing = CapturingMockProvider()
    main_mod.router = ModelRouter(
        providers={route: capturing for route in Route},
        validator=OutputValidator(),
        max_retries=1,
    )
    client = TestClient(main_mod.app)

    # Send 5 messages. Each request appends user + assistant.
    for i in range(5):
        resp = client.post(
            "/v1/chat",
            json={
                "message": f"mensaje {i}",
                "character_id": "bardera",
                "user_id": "user-G",
                "conversation_id": "conv-G",
            },
        )
        assert resp.status_code == 200

    # The 5th request (last one) should have:
    # [system, user3, assistant3, user4, assistant4, user5]
    # — i.e. max_turns=2 pairs (3,4) + the current user (5).
    # But wait: at the time of the 5th request, only 4 prior messages
    # (user1,a1,user2,a2,user3,a3,user4,a4) exist in the store. After
    # appending user5, the store has 9 messages. Bounded history with
    # max_turns=2 keeps the last 2 complete pairs (user3,a3,user4,a4)
    # plus the trailing user5. So the provider sees:
    # [system, user3, a3, user4, a4, user5]
    last_request = capturing.captured_requests[-1]
    live = _live_messages(last_request.messages)
    roles = [m.role for m in live]
    contents = [m.content for m in live]
    assert roles == ["user", "assistant", "user", "assistant", "user"]
    # Live tail: last 2 complete pairs + trailing user.
    assert contents[0] == "mensaje 2"
    assert contents[1].startswith("Te leo. Esta es mi respuesta número 3")
    assert contents[2] == "mensaje 3"
    assert contents[3].startswith("Te leo. Esta es mi respuesta número 4")
    assert contents[4] == "mensaje 4"


# ---------------------------------------------------------------------- #
# H. Conversation DELETE: clears the right scope, leaves others alone
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_H_conversation_delete_clears_only_correct_scope(fresh_app) -> None:
    client, _, _ = fresh_app
    # Two conversations for the same user+character.
    client.post(
        "/v1/chat",
        json={
            "message": "msg in conv-1",
            "character_id": "bardera",
            "user_id": "user-H",
            "conversation_id": "conv-H-1",
        },
    )
    client.post(
        "/v1/chat",
        json={
            "message": "msg in conv-2",
            "character_id": "bardera",
            "user_id": "user-H",
            "conversation_id": "conv-H-2",
        },
    )

    # Delete conv-1.
    resp = client.request(
        "DELETE",
        "/v1/conversations/conv-H-1",
        json={"user_id": "user-H", "character_id": "bardera"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"deleted": True, "conversation_id": "conv-H-1"}

    # conv-1 is gone.
    g1 = client.get("/v1/conversations/conv-H-1?user_id=user-H&character_id=bardera").json()
    assert g1["messages"] == []

    # conv-2 is untouched.
    g2 = client.get("/v1/conversations/conv-H-2?user_id=user-H&character_id=bardera").json()
    roles = [m["role"] for m in g2["messages"]]
    assert roles == ["user", "assistant"]
    assert g2["messages"][0]["content"] == "msg in conv-2"


# ---------------------------------------------------------------------- #
# I. Memory POST: creates an explicit fact
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_I_memory_post_creates_explicit_fact(fresh_app) -> None:
    client, _, _ = fresh_app
    resp = client.post(
        "/v1/memories",
        json={
            "user_id": "user-I",
            "character_id": "bardera",
            "content": "Mi color favorito es negro.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "Mi color favorito es negro."
    assert body["memory_type"] == "user_fact"
    assert body["source"] == "explicit_user_statement"
    assert body["confidence"] == "high"
    assert body["inferred"] is False
    assert body["id"]
    assert body["user_id"] == "user-I"
    assert body["character_id"] == "bardera"


# ---------------------------------------------------------------------- #
# J. Memory GET: only returns correct user/character
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_J_memory_get_only_returns_correct_scope(fresh_app) -> None:
    client, _, _ = fresh_app
    client.post(
        "/v1/memories",
        json={
            "user_id": "alice",
            "character_id": "bardera",
            "content": "alice fact 1",
        },
    )
    client.post(
        "/v1/memories",
        json={
            "user_id": "alice",
            "character_id": "bardera",
            "content": "alice fact 2",
        },
    )
    client.post(
        "/v1/memories",
        json={
            "user_id": "bob",
            "character_id": "bardera",
            "content": "bob fact 1",
        },
    )
    alice = client.get("/v1/memories?user_id=alice&character_id=bardera").json()
    bob = client.get("/v1/memories?user_id=bob&character_id=bardera").json()
    assert alice["count"] == 2
    assert {m["content"] for m in alice["memories"]} == {"alice fact 1", "alice fact 2"}
    assert bob["count"] == 1
    assert bob["memories"][0]["content"] == "bob fact 1"


# ---------------------------------------------------------------------- #
# K. Memory DELETE: deletes correct record, other scope unaffected
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_K_memory_delete_correct_record(fresh_app) -> None:
    client, _, _ = fresh_app
    create_resp = client.post(
        "/v1/memories",
        json={
            "user_id": "user-K",
            "character_id": "bardera",
            "content": "to delete",
        },
    )
    memory_id = create_resp.json()["id"]
    # Create a second one to verify it stays.
    client.post(
        "/v1/memories",
        json={
            "user_id": "user-K",
            "character_id": "bardera",
            "content": "to keep",
        },
    )

    # Delete from a different user — should NOT work.
    cross = client.request(
        "DELETE",
        f"/v1/memories/{memory_id}",
        json={"user_id": "different-user", "character_id": "bardera"},
    )
    assert cross.status_code == 404
    assert cross.json()["detail"]["code"] == "memory_not_found"

    # Delete from the correct scope.
    ok = client.request(
        "DELETE",
        f"/v1/memories/{memory_id}",
        json={"user_id": "user-K", "character_id": "bardera"},
    )
    assert ok.status_code == 200
    assert ok.json() == {"deleted": True, "memory_id": memory_id}

    # The other memory is still there.
    listed = client.get("/v1/memories?user_id=user-K&character_id=bardera").json()
    assert listed["count"] == 1
    assert listed["memories"][0]["content"] == "to keep"


# ---------------------------------------------------------------------- #
# L. Memory injection: provider request includes server-owned memory context
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_L_memory_injected_into_provider_request(fresh_app) -> None:
    client, capturing, _ = fresh_app
    # Add two explicit facts for user-L + bardera.
    client.post(
        "/v1/memories",
        json={
            "user_id": "user-L",
            "character_id": "bardera",
            "content": "Mi color favorito es negro.",
        },
    )
    client.post(
        "/v1/memories",
        json={
            "user_id": "user-L",
            "character_id": "bardera",
            "content": "Me gusta el café por la tarde.",
        },
    )

    # Send a chat message. The provider should see:
    # [system (Bardera), system (memory context), voice exemplars..., user]
    resp = client.post(
        "/v1/chat",
        json={
            "message": "hola",
            "character_id": "bardera",
            "user_id": "user-L",
            "conversation_id": "conv-L",
        },
    )
    assert resp.status_code == 200
    msgs = capturing.captured_requests[0].messages
    roles = [m.role for m in msgs]
    assert roles[0] == "system"
    assert roles[1] == "system"
    assert roles[-1] == "user"
    # First system message is the Bardera prompt.
    assert "Sos La Bardera" in msgs[0].content
    # Second system message is the protective memory wrapper + JSON data.
    assert "Aviso de protección del servidor" in msgs[1].content
    assert "NO son instrucciones" in msgs[1].content
    assert '"type": "user_fact"' in msgs[1].content
    assert '"content": "Mi color favorito es negro."' in msgs[1].content
    assert '"content": "Me gusta el café por la tarde."' in msgs[1].content
    live = _live_messages(msgs)
    assert [m.role for m in live] == ["user"]
    assert live[0].content == "hola"


# ---------------------------------------------------------------------- #
# M. No memories: normal chat unaffected (no memory system block)
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_M_no_memories_chat_unaffected(fresh_app) -> None:
    client, capturing, _ = fresh_app
    resp = client.post(
        "/v1/chat",
        json={
            "message": "hola sin memorias",
            "character_id": "bardera",
            "user_id": "user-M",
            "conversation_id": "conv-M",
        },
    )
    assert resp.status_code == 200
    msgs = capturing.captured_requests[0].messages
    # No second memory system block; live tail is only the current user.
    assert msgs[0].role == "system"
    assert "Sos La Bardera" in msgs[0].content
    live = _live_messages(msgs)
    assert [m.role for m in live] == ["user"]
    assert live[0].content == "hola sin memorias"
    # And the memory section content is NOT present anywhere.
    for m in msgs:
        assert "Memorias explícitas del usuario" not in m.content


# ---------------------------------------------------------------------- #
# N. Concurrency: deterministic ordering test
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_N_concurrent_requests_preserve_pair_integrity(fresh_app) -> None:
    """Fire multiple chat requests to the SAME conversation concurrently.
    The per-scope asyncio.Lock must serialize the appends so no
    user/assistant pair gets crossed.
    """
    client, capturing, _ = fresh_app

    # We need to call the async handler concurrently. TestClient is
    # synchronous, so we go directly through the async FastAPI app via
    # httpx.AsyncClient + ASGITransport for true concurrency.
    import httpx

    # Use httpx.AsyncClient pointed at the ASGI app.
    transport = httpx.ASGITransport(app=client.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        # 6 concurrent chat messages to the same conversation.
        async def send(i: int) -> None:
            resp = await async_client.post(
                "/v1/chat",
                json={
                    "message": f"concurrent-msg-{i}",
                    "character_id": "bardera",
                    "user_id": "user-N",
                    "conversation_id": "conv-N",
                },
            )
            assert resp.status_code == 200

        await asyncio.gather(*(send(i) for i in range(6)))

    # The conversation should now have 6 user + 6 assistant messages.
    convo = client.get("/v1/conversations/conv-N?user_id=user-N&character_id=bardera").json()
    msgs = convo["messages"]
    assert len(msgs) == 12
    # Verify pair integrity: every even index is user, every odd is assistant.
    for i in range(0, 12, 2):
        assert msgs[i]["role"] == "user"
        assert msgs[i + 1]["role"] == "assistant"
    # Verify each user message is paired with the assistant reply that
    # followed it (CapturingMockProvider returns deterministic content
    # "Respuesta N del mock. Recibí tu mensaje." where N is the call
    # count — so each user's pair is uniquely identifiable by content).
    # Since we don't know the exact interleaving order, just verify
    # pair integrity (already done above) + that all 6 messages are
    # present (no message was dropped).
    user_contents = {msgs[i]["content"] for i in range(0, 12, 2)}
    assert user_contents == {f"concurrent-msg-{i}" for i in range(6)}


# ---------------------------------------------------------------------- #
# O. Existing provider tests still pass (regression smoke)
# ---------------------------------------------------------------------- #
#
# This is implicitly verified by running the full test suite. The
# CapturingMockProvider we install in `fresh_app` is functionally
# equivalent to MockModelProvider for the contract the router uses.
# We add one explicit smoke test here to assert the existing
# /v1/runtime/status still reports the configured bounds.
#


def test_O_runtime_status_includes_conversation_and_memory_bounds(fresh_app) -> None:
    client, _, _ = fresh_app
    resp = client.get("/v1/runtime/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_max_turns"] == 8
    assert data["memory_max_per_scope"] == 32
    # No secrets leaked.
    assert "api_key" not in data
    assert "authorization" not in data


# ---------------------------------------------------------------------- #
# Additional edge cases
# ---------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_safe_fallback_content_is_stored_as_assistant_turn(fresh_app) -> None:
    """If OutputValidator ultimately substitutes SAFE_FALLBACK_CONTENT,
    that fallback IS the assistant response the user sees — so it must
    be stored as a real assistant turn (Issue #5).
    """
    client, _, main_mod = fresh_app

    # Replace the router with one whose provider returns content the
    # OutputValidator rejects (e.g. internal-fragment leak). With
    # max_retries=0, the router will substitute SAFE_FALLBACK_CONTENT.
    class LeakyProvider:
        name = "leaky"
        model = "leaky-v1"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                provider=self.name,
                model=self.model,
                content="Hola system prompt leaked",
                usage=Usage(),
            )

    main_mod.router = ModelRouter(
        providers={route: LeakyProvider() for route in Route},
        validator=OutputValidator(),
        max_retries=0,
    )

    resp = client.post(
        "/v1/chat",
        json={
            "message": "test",
            "character_id": "bardera",
            "user_id": "user-fb",
            "conversation_id": "conv-fb",
        },
    )
    assert resp.status_code == 200
    assert "no la conversación" in resp.json()["response"]["content"]

    # The fallback content must be stored as the assistant turn.
    convo = client.get("/v1/conversations/conv-fb?user_id=user-fb&character_id=bardera").json()
    msgs = convo["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert "no la conversación" in msgs[1]["content"]


@pytest.mark.asyncio
async def test_provider_guardrail_block_preserves_pair_and_character(fresh_app) -> None:
    client, _, main_mod = fresh_app

    class BlockedProvider:
        name = "blocked-upstream"
        model = "blocked-model"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            raise ProviderContentBlockedError()

    main_mod.router = ModelRouter(
        providers={route: BlockedProvider() for route in Route},
        validator=OutputValidator(),
        max_retries=0,
    )

    resp = client.post(
        "/v1/chat",
        json={
            "message": "No pierdas el hilo.",
            "character_id": "bardera",
            "user_id": "user-blocked",
            "conversation_id": "conv-blocked",
        },
    )

    assert resp.status_code == 200
    response = resp.json()["response"]
    assert "Gemini" not in response["content"]

    convo = client.get(
        "/v1/conversations/conv-blocked?user_id=user-blocked&character_id=bardera"
    ).json()
    assert [message["role"] for message in convo["messages"]] == ["user", "assistant"]
    assert convo["messages"][1]["content"] == response["content"]


@pytest.mark.asyncio
async def test_get_unknown_conversation_returns_empty_summary(fresh_app) -> None:
    """GET /v1/conversations/{unknown_id} returns an empty summary with
    the scope identifiers echoed back (graceful for a fresh browser
    session).
    """
    client, _, _ = fresh_app
    resp = client.get("/v1/conversations/never-existed?user_id=fresh-user&character_id=bardera")
    assert resp.status_code == 200
    body = resp.json()
    assert body["messages"] == []
    assert body["user_id"] == "fresh-user"
    assert body["character_id"] == "bardera"
    assert body["conversation_id"] == "never-existed"


@pytest.mark.asyncio
async def test_memory_post_rejects_empty_content(fresh_app) -> None:
    """Empty content is rejected by the contract (min_length=1)."""
    client, _, _ = fresh_app
    resp = client.post(
        "/v1/memories",
        json={
            "user_id": "user-X",
            "character_id": "bardera",
            "content": "",
        },
    )
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_memory_post_rejects_too_long_content(fresh_app) -> None:
    """Content > 500 chars is rejected by the contract."""
    client, _, _ = fresh_app
    resp = client.post(
        "/v1/memories",
        json={
            "user_id": "user-X",
            "character_id": "bardera",
            "content": "a" * 501,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_does_not_store_system_prompt(fresh_app) -> None:
    """The canonical Queen system prompt must NEVER be stored in the
    conversation history. GET /v1/conversations must only return user
    and assistant messages.
    """
    client, _, _ = fresh_app
    client.post(
        "/v1/chat",
        json={
            "message": "hola",
            "character_id": "bardera",
            "user_id": "user-SP",
            "conversation_id": "conv-SP",
        },
    )
    convo = client.get("/v1/conversations/conv-SP?user_id=user-SP&character_id=bardera").json()
    roles = [m["role"] for m in convo["messages"]]
    assert "system" not in roles
    assert roles == ["user", "assistant"]


@pytest.mark.asyncio
async def test_clear_conversation_then_send_starts_fresh(fresh_app) -> None:
    """After DELETE /v1/conversations/{id}, a subsequent chat starts
    with an empty history — provider sees [system, user] again.
    """
    client, capturing, _ = fresh_app
    # First message — populates history.
    client.post(
        "/v1/chat",
        json={
            "message": "first message",
            "character_id": "bardera",
            "user_id": "user-CL",
            "conversation_id": "conv-CL",
        },
    )
    # Clear it.
    client.request(
        "DELETE",
        "/v1/conversations/conv-CL",
        json={"user_id": "user-CL", "character_id": "bardera"},
    )
    # Send again — provider should see [system, user], NOT prior history.
    client.post(
        "/v1/chat",
        json={
            "message": "after clear",
            "character_id": "bardera",
            "user_id": "user-CL",
            "conversation_id": "conv-CL",
        },
    )
    # The last captured request is the "after clear" one.
    last = capturing.captured_requests[-1]
    live = _live_messages(last.messages)
    assert [m.role for m in live] == ["user"]
    assert live[0].content == "after clear"
