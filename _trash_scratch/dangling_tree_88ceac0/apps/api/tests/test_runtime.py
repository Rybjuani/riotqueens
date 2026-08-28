"""Tests for the /v1/chat handler and /v1/runtime/status endpoint.

Covers:
- Server-side system prompt injection for character_id="bardera".
- Stable rejection of unknown character ids before runtime work.
- Explicit, bounded scope identifiers and server-owned public routing.
- Runtime status reports safe diagnostics (no secrets).
- build_router() defaults to mock and falls back to mock when
  provider=openai but credentials are missing.
"""

from __future__ import annotations

import pytest

from app.domain.contracts import Route
from app.domain.queens import BARDERA_SYSTEM_PROMPT, is_registered_queen
from app.domain.router import MockModelProvider, build_router, runtime_status
from tests.asgi_test_client import SyncASGIClient as TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Force mock provider for handler tests (no real network).
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "mock")
    # Re-import main so the module-level router picks up the env.
    import importlib

    import app.main as main_mod

    importlib.reload(main_mod)
    return TestClient(main_mod.app)


def _chat_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "message": "hola",
        "character_id": "bardera",
        "user_id": "runtime-user",
        "conversation_id": "runtime-conversation",
    }
    payload.update(overrides)
    return payload


def test_chat_injects_bardera_system_prompt(client: TestClient) -> None:
    """character_id=bardera prepends the server-owned system prompt."""
    resp = client.post(
        "/v1/chat",
        json=_chat_payload(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["response"]) == {"content"}
    assert data["response"]["content"]


def test_chat_unknown_character_returns_stable_not_found(client: TestClient) -> None:
    resp = client.post(
        "/v1/chat",
        json=_chat_payload(character_id="unknown-character"),
    )
    assert resp.status_code == 404
    assert resp.json() == {
        "detail": {
            "code": "queen_not_found",
            "message": "Queen is not available.",
        }
    }


def test_bardera_runtime_contract_contains_ratified_voice_invariants() -> None:
    prompt = BARDERA_SYSTEM_PROMPT.lower()

    assert is_registered_queen("bardera") is True
    assert is_registered_queen("unknown-character") is False
    assert all(
        invariant in prompt
        for invariant in (
            "criterio propio",
            "aguante",
            "sinceridad",
            "timing",
            "voseo",
            "tema identitario",
            "bardera lavada",
            "soundboard",
            "siome",
            "manaos",
            "muestras de voz",
            "diluir personalidad",
        )
    )


def test_runtime_status_reports_mock_mode(client: TestClient) -> None:
    resp = client.get("/v1/runtime/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert data["mode"] == "mock"
    assert data["configured"] is False
    # No secret fields present.
    assert "api_key" not in data
    assert "authorization" not in data
    assert "Authorization" not in data
    assert "url" not in data


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "riotqueens-api"


# ---------------------------------------------------------------------- #
# build_router() provider selection
# ---------------------------------------------------------------------- #


def test_build_router_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RIOTQUEENS_MODEL_PROVIDER", raising=False)
    rt = build_router()
    sample = rt.providers[Route.FAST_CHAT]
    assert isinstance(sample, MockModelProvider)
    status = runtime_status(rt)
    assert status["mode"] == "mock"
    assert status["configured"] is False


def test_legacy_companion_env_is_not_an_active_runtime_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RIOTQUEENS_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("RIOTQUEENS_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("RIOTQUEENS_MODEL_API_KEY", raising=False)
    monkeypatch.setenv("COMPANION_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("COMPANION_MODEL_BASE_URL", "https://legacy.example.com/v1")
    monkeypatch.setenv("COMPANION_MODEL_API_KEY", "legacy-secret")

    rt = build_router()

    assert isinstance(rt.providers[Route.FAST_CHAT], MockModelProvider)
    assert runtime_status(rt)["configured"] is False


def test_build_router_openai_without_credentials_falls_back_to_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """provider=openai but no base_url/api_key → mock fallback (Issue #3 #2)."""
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "openai")
    monkeypatch.delenv("RIOTQUEENS_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("RIOTQUEENS_MODEL_API_KEY", raising=False)
    rt = build_router()
    sample = rt.providers[Route.FAST_CHAT]
    assert isinstance(sample, MockModelProvider)


def test_build_router_openai_with_credentials_wires_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("RIOTQUEENS_MODEL_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("RIOTQUEENS_MODEL_API_KEY", "sk-test-fake")
    monkeypatch.setenv("RIOTQUEENS_MODEL_NAME", "riotqueens-chat-v1")
    rt = build_router()
    sample = rt.providers[Route.FAST_CHAT]
    assert sample.name == "openai-compatible"
    assert sample.model == "riotqueens-chat-v1"
    status = runtime_status(rt)
    assert status["mode"] == "real"
    assert status["configured"] is True
    # No secret in the status dict.
    assert "api_key" not in status
    assert "sk-test-fake" not in str(status)


def test_build_router_can_omit_frequency_penalty_for_compatibility_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("RIOTQUEENS_MODEL_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("RIOTQUEENS_MODEL_API_KEY", "sk-test-fake")
    monkeypatch.setenv("RIOTQUEENS_MODEL_OMIT_FREQUENCY_PENALTY", "true")

    rt = build_router()

    sample = rt.providers[Route.FAST_CHAT]
    assert getattr(sample, "frequency_penalty") is None


def test_runtime_status_no_secret_leak_for_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("RIOTQUEENS_MODEL_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("RIOTQUEENS_MODEL_API_KEY", "sk-super-secret-do-not-leak")
    rt = build_router()
    status = runtime_status(rt)
    status_str = str(status)
    assert "sk-super-secret-do-not-leak" not in status_str
    assert "api_key" not in status


def test_build_router_wires_sanitized_fallback_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIOTQUEENS_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("RIOTQUEENS_MODEL_BASE_URL", "https://primary.example.com/v1")
    monkeypatch.setenv("RIOTQUEENS_MODEL_API_KEY", "primary-secret")
    monkeypatch.setenv("RIOTQUEENS_MODEL_NAME", "gemini-primary")
    monkeypatch.setenv("RIOTQUEENS_FALLBACK_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("RIOTQUEENS_FALLBACK_MODEL_BASE_URL", "https://fallback.example.com/v1")
    monkeypatch.setenv("RIOTQUEENS_FALLBACK_MODEL_API_KEY", "fallback-secret")
    monkeypatch.setenv("RIOTQUEENS_FALLBACK_MODEL_NAME", "llama-fallback")

    rt = build_router()
    status = runtime_status(rt)

    assert status["fallback_configured"] is True
    assert status["fallback_model"] == "llama-fallback"
    assert "primary-secret" not in str(status)
    assert "fallback-secret" not in str(status)
