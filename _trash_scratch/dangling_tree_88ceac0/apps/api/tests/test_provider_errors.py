"""Retry semantics and safe HTTP mapping for typed provider failures."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from app.domain.contracts import MessageInput, ModelRequest, ModelResponse, Route
from app.domain.providers.errors import (
    ProviderAuthError,
    ProviderConnectError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
)
from app.domain.router import ModelRouter
from tests.asgi_test_client import SyncASGIClient as TestClient


class SequenceProvider:
    name = "sequence"
    model = "test-model"

    def __init__(self, outcomes: Sequence[Exception | ModelResponse]) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    async def generate(self, _request: ModelRequest) -> ModelResponse:
        outcome = self.outcomes[min(self.calls, len(self.outcomes) - 1)]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome.model_copy(deep=True)


def _request() -> ModelRequest:
    return ModelRequest(
        route=Route.FAST_CHAT,
        character_id="queen-test",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )


def _ok(content: str = "Hola, ahora funciona bien.") -> ModelResponse:
    return ModelResponse(provider="sequence", model="test-model", content=content)


def _router(provider: SequenceProvider, *, retries: int = 1) -> ModelRouter:
    return ModelRouter(
        providers={route: provider for route in Route},
        max_retries=retries,
        timeout_seconds=1.0,
    )


@pytest.mark.asyncio
async def test_429_then_success_retries_and_returns_real_content() -> None:
    provider = SequenceProvider([ProviderRateLimitError(), _ok()])
    response = await _router(provider).generate(_request())
    assert provider.calls == 2
    assert response.content == "Hola, ahora funciona bien."
    assert response.retry_count == 1


@pytest.mark.asyncio
async def test_5xx_then_success_retries_and_returns_real_content() -> None:
    provider = SequenceProvider([ProviderServerError(), _ok("Hola, ya volvió el servicio.")])
    response = await _router(provider).generate(_request())
    assert provider.calls == 2
    assert response.content == "Hola, ya volvió el servicio."
    assert response.retry_count == 1


def _client_with_provider(provider: SequenceProvider, *, retries: int = 1) -> TestClient:
    import app.main as main_mod

    main_mod.router = _router(provider, retries=retries)
    return TestClient(main_mod.app, raise_server_exceptions=False)


def _chat_payload() -> dict[str, str]:
    return {
        "message": "hola",
        "character_id": "bardera",
        "user_id": "provider-error-user",
        "conversation_id": "provider-error-conversation",
    }


def test_timeout_exhaustion_maps_to_504() -> None:
    provider = SequenceProvider([ProviderTimeoutError()])
    response = _client_with_provider(provider, retries=1).post(
        "/v1/chat", json=_chat_payload()
    )
    assert provider.calls == 2
    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "provider_timeout"


def test_connect_exhaustion_maps_to_503() -> None:
    provider = SequenceProvider([ProviderConnectError()])
    response = _client_with_provider(provider, retries=1).post(
        "/v1/chat", json=_chat_payload()
    )
    assert provider.calls == 2
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_connect_failed"


@pytest.mark.parametrize("error", [ProviderAuthError(), ProviderAuthError()])
def test_provider_auth_error_does_not_retry_or_expose_upstream_auth(error: Exception) -> None:
    provider = SequenceProvider([error])
    response = _client_with_provider(provider, retries=3).post(
        "/v1/chat", json=_chat_payload()
    )
    assert provider.calls == 1
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_config_error"
    assert response.status_code not in (401, 403)


def test_invalid_upstream_response_is_bounded_retry_then_502() -> None:
    provider = SequenceProvider([ProviderInvalidResponseError()])
    response = _client_with_provider(provider, retries=1).post(
        "/v1/chat", json=_chat_payload()
    )
    assert provider.calls == 2
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "provider_invalid_response"


@pytest.mark.parametrize(
    "error",
    [
        ProviderTimeoutError(),
        ProviderConnectError(),
        ProviderRateLimitError(),
        ProviderServerError(),
        ProviderInvalidResponseError(),
        ProviderAuthError(),
    ],
)
def test_error_responses_never_leak_secret_material(error: Exception) -> None:
    provider = SequenceProvider([error])
    response = _client_with_provider(provider, retries=0).post(
        "/v1/chat", json=_chat_payload()
    )
    body = response.text.lower()
    assert response.headers["cache-control"] == "no-store"
    assert "authorization" not in body
    assert "bearer" not in body
    assert "sk-super-secret-do-not-leak" not in body
    assert "traceback" not in body
    assert "api.example.com" not in body
