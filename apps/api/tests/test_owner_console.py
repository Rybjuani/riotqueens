"""Owner Console — gate, root raw path, compare diff, public chat unchanged."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.domain.contracts import MessageInput, ModelRequest, ModelResponse, Route
from app.domain.providers.errors import ProviderUpstreamError
from app.domain.providers.openai_compatible import OpenAICompatibleProvider
from app.domain.queens import BARDERA_SYSTEM_PROMPT
from app.domain.router import MockModelProvider, ModelRouter
from tests.asgi_test_client import SyncASGIClient as TestClient


def _reload_main(monkeypatch: pytest.MonkeyPatch, **env: str):
    monkeypatch.setenv("RIOTQUEENS_AUTH_ENABLED", env.get("RIOTQUEENS_AUTH_ENABLED", "false"))
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", env.get("RIOTQUEENS_MODEL_PROVIDER", "mock"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for key in (
        "RIOTQUEENS_OWNER_AUTH0_SUBJECTS",
        "RIOTQUEENS_OWNER_USER_IDS",
    ):
        if key in env:
            monkeypatch.setenv(key, env[key])
        else:
            monkeypatch.delenv(key, raising=False)

    import importlib

    import app.main as main_mod

    importlib.reload(main_mod)
    return main_mod


def test_owner_gate_fail_closed_without_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch)
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c1",
            "user_id": "smoke",
            "message": "hola",
            "system": "empty",
        },
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "owner_forbidden"


def test_owner_console_accepts_private_loopback_web_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    """The tunnelled UI is allowed without widening the public Caddy surface."""
    monkeypatch.setenv("RIOTQUEENS_CORS_ORIGINS", "https://riotqueens.live")
    main_mod = _reload_main(monkeypatch)
    client = TestClient(main_mod.app)
    res = client.request(
        "OPTIONS",
        "/v1/root/chat",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_owner_gate_rejects_unknown_user(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c1",
            "user_id": "intruder",
            "message": "hola",
            "system": "empty",
        },
    )
    assert res.status_code == 403


def test_root_empty_system_no_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    captured: dict[str, Any] = {}

    class CaptureMock(MockModelProvider):
        async def generate(self, request: ModelRequest) -> ModelResponse:
            captured["messages"] = [
                {"role": m.role, "content": m.content} for m in request.messages
            ]
            return await super().generate(request)

    main_mod.router = ModelRouter(
        providers={Route.FAST_CHAT: CaptureMock()},
        max_retries=0,
    )
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c1",
            "user_id": "smoke",
            "message": "hola crudo",
            "system": "empty",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "owner" in body
    assert body["owner"]["channel"] == "root"
    assert body["owner"]["system"] == "empty"
    assert body["owner"]["local_guard"]["bypass"] is True
    assert body["owner"]["rewrite"]["applied"] is False
    assert body["owner"]["fallback"]["used"] is False
    roles = [m["role"] for m in captured["messages"]]
    assert "system" not in roles
    assert captured["messages"][-1]["content"] == "hola crudo"


def test_root_bardera_system_is_real_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    captured: dict[str, Any] = {}

    class CaptureMock(MockModelProvider):
        async def generate(self, request: ModelRequest) -> ModelResponse:
            captured["messages"] = list(request.messages)
            return await super().generate(request)

    main_mod.router = ModelRouter(
        providers={Route.FAST_CHAT: CaptureMock()},
        max_retries=0,
    )
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c2",
            "user_id": "smoke",
            "message": "hola",
            "system": "bardera",
        },
    )
    assert res.status_code == 200
    assert res.json()["owner"]["system"] == "bardera"
    assert captured["messages"][0].role == "system"
    assert captured["messages"][0].content == BARDERA_SYSTEM_PROMPT


def test_root_custom_system_no_diagnostic_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    captured: dict[str, Any] = {}

    class CaptureMock(MockModelProvider):
        async def generate(self, request: ModelRequest) -> ModelResponse:
            captured["messages"] = list(request.messages)
            return await super().generate(request)

    main_mod.router = ModelRouter(
        providers={Route.FAST_CHAT: CaptureMock()},
        max_retries=0,
    )
    client = TestClient(main_mod.app)
    custom = "Sos exactamente este personaje de prueba y nada más."
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c3",
            "user_id": "smoke",
            "message": "hola",
            "system": "custom",
            "custom_system": custom,
        },
    )
    assert res.status_code == 200
    assert captured["messages"][0].content == custom
    blob = " ".join(m.content for m in captured["messages"]).lower()
    assert "modo root" not in blob
    assert "reportá bloqueos" not in blob
    assert "reporta bloqueos" not in blob


def test_root_upstream_error_cartel(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            402,
            json={
                "error": {
                    "message": "Payment required for this model",
                    "code": "payment_required",
                    "type": "insufficient_credits",
                }
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://openrouter.example/api/v1",
        api_key="sk-test",
        model="sao10k/l3.3-euryale-70b",
        transport=httpx.MockTransport(handler),
        clamp_tokens=False,
        raw_errors=True,
        max_tokens=400,
    )
    main_mod.router = ModelRouter(
        providers={Route.FAST_CHAT: provider},
        max_retries=0,
    )
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c4",
            "user_id": "smoke",
            "message": "hola",
            "system": "empty",
        },
    )
    assert res.status_code == 502
    detail = res.json()["detail"]
    assert detail["code"] == "upstream_error"
    assert "Payment required" in detail["message"]
    assert detail["upstream"]["status"] == 402
    assert detail["upstream"]["error"]["code"] == "payment_required"
    assert detail["owner"]["channel"] == "root"
    assert detail["owner"]["local_guard"]["bypass"] is True


def test_root_cartel_redacts_key_management_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "message": "Key limit exceeded: https://openrouter.ai/workspaces/default/keys/sensitive-key-id"
                }
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://openrouter.example/api/v1",
        api_key="sk-test",
        model="sao10k/l3.3-euryale-70b",
        transport=httpx.MockTransport(handler),
        raw_errors=True,
    )
    main_mod.router = ModelRouter(providers={Route.FAST_CHAT: provider}, max_retries=0)
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/root/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "c-key-redaction",
            "user_id": "smoke",
            "message": "hola",
            "system": "empty",
        },
    )
    detail = res.json()["detail"]
    rendered = json.dumps(detail)
    assert res.status_code == 502
    assert "sensitive-key-id" not in rendered
    assert "/keys/[redacted]" in rendered


@pytest.mark.asyncio
async def test_root_provider_skips_fallback_chain() -> None:
    calls: list[str] = []

    class PrimaryBoom:
        name = "primary"
        model = "primary-model"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            calls.append("primary")
            raise ProviderUpstreamError(
                message="boom",
                upstream={"status": 500, "error": {"message": "boom"}},
            )

    class FallbackShouldNotRun:
        name = "fallback"
        model = "fallback-model"

        async def generate(self, request: ModelRequest) -> ModelResponse:
            calls.append("fallback")
            return ModelResponse(provider=self.name, model=self.model, content="nope")

    from app.domain.contracts import OwnerConsoleChatRequest
    from app.domain.conversations import InProcessConversationStore
    from app.domain.owner_console import run_root_turn

    router = ModelRouter(
        providers={Route.FAST_CHAT: PrimaryBoom()},  # type: ignore[arg-type]
        fallback_providers={Route.FAST_CHAT: (FallbackShouldNotRun(),)},  # type: ignore[arg-type]
        max_retries=0,
    )
    store = InProcessConversationStore(max_turns=8)
    payload = OwnerConsoleChatRequest(
        character_id="bardera",
        conversation_id="c5",
        user_id="smoke",
        message="hola",
        system="empty",
        persist=False,
    )
    with pytest.raises(ProviderUpstreamError):
        await run_root_turn(
            router=router,
            conversation_store=store,
            user_id="smoke",
            payload=payload,
        )
    assert calls == ["primary"]


def test_usuario_includes_owner_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/usuario/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "u1",
            "user_id": "smoke",
            "message": "hola",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response"]["content"]
    assert body["owner"]["channel"] == "usuario"
    assert body["owner"]["system"] == "bardera"
    assert body["owner"]["rewrite"]["applied"] is True


def test_compare_diff_system_usuario_bardera_root_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/compare",
        json={
            "character_id": "bardera",
            "conversation_id": "cmp1",
            "user_id": "smoke",
            "message": "hola",
            "system": "empty",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["diff"]["system"]["usuario"] == "bardera"
    assert body["diff"]["system"]["root"] == "empty"
    assert body["diff"]["local_guard"]["root"] == "bypass"
    assert body["diff"]["rewrite"]["usuario"] is True
    assert body["diff"]["rewrite"]["root"] is False
    assert body["usuario"]["content"]
    assert body["root"]["content"]
    assert body["errors"]["usuario"] is None
    assert body["errors"]["root"] is None


def test_public_chat_has_no_owner_field(monkeypatch: pytest.MonkeyPatch) -> None:
    main_mod = _reload_main(monkeypatch, RIOTQUEENS_OWNER_USER_IDS="smoke")
    client = TestClient(main_mod.app)
    res = client.post(
        "/v1/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "pub1",
            "user_id": "anyone",
            "message": "hola",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "owner" not in body
    assert "response" in body


@pytest.mark.asyncio
async def test_raw_provider_no_clamp() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model="test",
        transport=httpx.MockTransport(handler),
        max_tokens=420,
        clamp_tokens=False,
        raw_errors=True,
    )
    await provider.generate(
        ModelRequest(
            route=Route.FAST_CHAT,
            character_id="bardera",
            user_id="u",
            conversation_id="c",
            messages=[MessageInput(role="user", content="hola")],
        )
    )
    assert captured["body"]["max_tokens"] == 420
    await provider.aclose()
