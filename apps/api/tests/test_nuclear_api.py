"""Honest tests for the nuclear API — no cape / no SAFE_FALLBACK substitution."""

from __future__ import annotations

import json

import httpx
import pytest

from app.domain.contracts import MessageInput, ModelRequest, Route
from app.domain.providers.openai_compatible import (
    OpenAICompatibleProvider,
    clamp_max_tokens,
)
from app.domain.queens import BARDERA_SYSTEM_PROMPT, get_system_prompt, is_registered_queen
from app.domain.router import ModelRouter, MockModelProvider
from tests.asgi_test_client import SyncASGIClient as TestClient


def test_clamp_max_tokens_t1_band() -> None:
    assert clamp_max_tokens(50) == 180
    assert clamp_max_tokens(200) == 200
    assert clamp_max_tokens(999) == 220


def test_dossier_maestro_loaded_for_bardera() -> None:
    assert is_registered_queen("bardera")
    prompt = get_system_prompt("bardera") or ""
    assert prompt == BARDERA_SYSTEM_PROMPT
    low = prompt.lower()
    assert "criterio propio" in low or "criterio" in low
    assert "bardera" in low
    # Full dossier — no 80/90-line cape.
    assert BARDERA_SYSTEM_PROMPT.count("\n") > 90


@pytest.mark.asyncio
async def test_payload_includes_max_tokens() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "Hola bobo."}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model="test",
        transport=httpx.MockTransport(handler),
        max_tokens=50,
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
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["max_tokens"] == 180
    await provider.aclose()


@pytest.mark.asyncio
async def test_router_does_not_substitute_safe_fallback_for_refusal_text() -> None:
    """CLEAN §1: 'no puedo ayudar…' from a model is not replaced by a fake Bardera line."""

    class RefusalProvider:
        name = "refusal"
        model = "refusal-v1"

        async def generate(self, request: ModelRequest) -> object:
            from app.domain.contracts import ModelResponse

            return ModelResponse(
                provider=self.name,
                model=self.model,
                content="No puedo ayudar con eso en esta conversación.",
            )

    router = ModelRouter(
        providers={Route.FAST_CHAT: RefusalProvider()},  # type: ignore[arg-type]
        max_retries=0,
    )
    response = await router.generate(
        ModelRequest(
            route=Route.FAST_CHAT,
            character_id="bardera",
            user_id="u",
            conversation_id="c",
            messages=[MessageInput(role="user", content="hola")],
        )
    )
    assert "No puedo ayudar" in response.content
    assert "CONTINUITY" not in response.content
    assert response.provider == "refusal"


@pytest.mark.asyncio
async def test_router_passes_mock_content() -> None:
    router = ModelRouter(providers={Route.FAST_CHAT: MockModelProvider()}, max_retries=0)
    response = await router.generate(
        ModelRequest(
            route=Route.FAST_CHAT,
            character_id="bardera",
            user_id="u",
            conversation_id="c",
            messages=[MessageInput(role="user", content="qué hacés")],
        )
    )
    assert "(mock)" in response.content


def test_health_and_chat_preauth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOTQUEENS_AUTH_ENABLED", "false")
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "mock")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import importlib

    import app.main as main_mod

    importlib.reload(main_mod)
    client = TestClient(main_mod.app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    chat = client.post(
        "/v1/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "t1",
            "user_id": "smoke",
            "message": "hola",
        },
    )
    assert chat.status_code == 200
    content = chat.json()["response"]["content"]
    assert content
    assert "CONTINUITY" not in content


def test_chat_requires_auth_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOTQUEENS_AUTH_ENABLED", "true")
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "mock")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import importlib

    import app.main as main_mod

    importlib.reload(main_mod)
    client = TestClient(main_mod.app)
    chat = client.post(
        "/v1/chat",
        json={
            "character_id": "bardera",
            "conversation_id": "t1",
            "user_id": "smoke",
            "message": "hola",
        },
    )
    assert chat.status_code == 401
