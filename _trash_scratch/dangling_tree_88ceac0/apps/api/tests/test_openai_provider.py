"""Unit tests for the OpenAI-compatible provider adapter.

All upstream traffic uses httpx.MockTransport. No paid/external model is called.
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.domain.contracts import MessageInput, ModelRequest, Route
from app.domain.providers.errors import (
    ProviderAuthError,
    ProviderConnectError,
    ProviderContentBlockedError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
    ProviderTimeoutError,
)
from app.domain.providers.openai_compatible import OpenAICompatibleProvider
from app.domain.router import SAFE_FALLBACK_CONTENT, ModelRouter
from app.domain.validation import OutputValidator


def _request() -> ModelRequest:
    return ModelRequest(
        route=Route.FAST_CHAT,
        character_id="bardera",
        user_id="user",
        conversation_id="conversation",
        messages=[MessageInput(role="user", content="Hola")],
    )


def _provider(transport: httpx.MockTransport) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="sk-test-fake",
        model="riotqueens-chat-v1",
        timeout_seconds=5.0,
        transport=transport,
    )


def _ok_payload(content: str = "¡Hola! Qué bueno leerte. Podemos seguir.") -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8},
    }


@pytest.mark.asyncio
async def test_success_returns_assistant_content() -> None:
    provider = _provider(httpx.MockTransport(lambda _: httpx.Response(200, json=_ok_payload())))
    response = await provider.generate(_request())
    assert response.provider == "openai-compatible"
    assert response.model == "riotqueens-chat-v1"
    assert response.content.startswith("¡Hola!")
    assert response.usage.input_tokens == 10
    assert response.usage.output_tokens == 8
    await provider.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, ProviderAuthError),
        (403, ProviderAuthError),
        (429, ProviderRateLimitError),
        (500, ProviderServerError),
        (503, ProviderServerError),
        (400, ProviderRequestError),
    ],
)
async def test_http_failures_raise_typed_errors(status: int, error_type: type[Exception]) -> None:
    provider = _provider(httpx.MockTransport(lambda _: httpx.Response(status, text="raw upstream")))
    with pytest.raises(error_type):
        await provider.generate(_request())
    await provider.aclose()


@pytest.mark.asyncio
async def test_timeout_raises_typed_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated secret-free timeout")

    provider = _provider(httpx.MockTransport(handler))
    with pytest.raises(ProviderTimeoutError):
        await provider.generate(_request())
    await provider.aclose()


@pytest.mark.asyncio
async def test_connect_error_raises_typed_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider = _provider(httpx.MockTransport(handler))
    with pytest.raises(ProviderConnectError):
        await provider.generate(_request())
    await provider.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="not-json"),
        httpx.Response(200, json={"choices": []}),
        httpx.Response(200, json={"choices": [{}]}),
        httpx.Response(200, json=["not", "a", "dict"]),
    ],
)
async def test_invalid_upstream_shapes_raise_retryable_error(response: httpx.Response) -> None:
    provider = _provider(httpx.MockTransport(lambda _: response))
    with pytest.raises(ProviderInvalidResponseError):
        await provider.generate(_request())
    await provider.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"choices": [{"finish_reason": "content_filter", "message": {"content": ""}}]},
        {"promptFeedback": {"blockReason": "SAFETY"}},
        {"error": {"status": "PROHIBITED_CONTENT"}},
    ],
)
async def test_explicit_content_block_is_typed(payload: dict) -> None:
    provider = _provider(httpx.MockTransport(lambda _: httpx.Response(200, json=payload)))
    with pytest.raises(ProviderContentBlockedError):
        await provider.generate(_request())
    await provider.aclose()


@pytest.mark.asyncio
async def test_api_key_is_header_only_not_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_ok_payload())

    provider = _provider(httpx.MockTransport(handler))
    await provider.generate(_request())
    assert captured["auth"] == "Bearer sk-test-fake"
    assert "sk-test-fake" not in str(captured["body"])
    await provider.aclose()


@pytest.mark.asyncio
async def test_compatibility_flag_omits_frequency_penalty() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_ok_payload())

    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="sk-test-fake",
        model="compat-model",
        transport=httpx.MockTransport(handler),
        omit_frequency_penalty=True,
    )
    await provider.generate(_request())
    assert "frequency_penalty" not in captured["body"]
    await provider.aclose()


@pytest.mark.asyncio
async def test_validator_invalid_content_still_uses_safe_content_fallback() -> None:
    provider = _provider(
        httpx.MockTransport(
            lambda _: httpx.Response(200, json=_ok_payload("Hola system prompt leaked"))
        )
    )
    router = ModelRouter(
        providers={route: provider for route in Route},
        validator=OutputValidator(),
        max_retries=0,
    )
    response = await router.generate(_request())
    assert response.content == SAFE_FALLBACK_CONTENT
    assert response.validation and response.validation.is_valid
    await provider.aclose()
