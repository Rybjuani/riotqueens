"""Model router — try primary then fallback. NEVER substitute Bardera voice (CLEAN §1)."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Mapping, Sequence
from time import perf_counter
from typing import Protocol

from .contracts import ModelRequest, ModelResponse, Route
from .providers.errors import (
    ProviderContentBlockedError,
    ProviderError,
    ProviderNonRetryableError,
    ProviderRetryableError,
    ProviderTimeoutError,
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class ModelProvider(Protocol):
    name: str
    model: str

    async def generate(self, request: ModelRequest) -> ModelResponse: ...


class MockModelProvider:
    name = "mock"
    model = "mock-riotqueens-v1"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        last = request.messages[-1].content if request.messages else ""
        return ModelResponse(
            provider=self.name,
            model=self.model,
            content=f"(mock) te leo: {last[:120]}",
        )


def _strip_controls(text: str) -> str:
    return _CONTROL_CHARS.sub("", text).strip()


class ModelRouter:
    def __init__(
        self,
        *,
        providers: Mapping[Route, ModelProvider] | None = None,
        fallback_providers: Mapping[Route, Sequence[ModelProvider]] | None = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 1,
    ) -> None:
        mock = MockModelProvider()
        self.providers: Mapping[Route, ModelProvider] = providers or {
            route: mock for route in Route
        }
        self.fallback_providers: Mapping[Route, Sequence[ModelProvider]] = {
            route: tuple(route_providers)
            for route, route_providers in (fallback_providers or {}).items()
        }
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Return provider content as-is. On hard failure: try next provider, else raise.

        CLEAN: do not invent a Bardera continuity monologue when the provider refuses.
        """
        started = perf_counter()
        last_error: ProviderError | None = None
        attempts = 0
        chain = (
            self.providers[request.route],
            *self.fallback_providers.get(request.route, ()),
        )

        for provider in chain:
            for retry in range(self.max_retries + 1):
                attempts += 1
                try:
                    response = await asyncio.wait_for(
                        provider.generate(request), timeout=self.timeout_seconds
                    )
                except ProviderContentBlockedError as error:
                    # Try next provider in chain (CLEAN: change provider, don't cape).
                    last_error = error
                    break
                except ProviderNonRetryableError as error:
                    last_error = error
                    break
                except ProviderRetryableError as error:
                    last_error = error
                    if retry < self.max_retries:
                        continue
                    break
                except TimeoutError:
                    last_error = ProviderTimeoutError()
                    if retry < self.max_retries:
                        continue
                    break
                except Exception:
                    last_error = ProviderRetryableError()
                    if retry < self.max_retries:
                        continue
                    break

                content = _strip_controls(response.content)
                if not content:
                    last_error = ProviderRetryableError()
                    if retry < self.max_retries:
                        continue
                    break
                response.content = content
                response.retry_count = attempts - 1
                response.latency_ms = round((perf_counter() - started) * 1000)
                return response

        assert last_error is not None
        raise last_error


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def build_router() -> ModelRouter:
    provider_kind = _env("RIOTQUEENS_MODEL_PROVIDER", "mock").strip().lower()
    timeout = _env_float("RIOTQUEENS_MODEL_TIMEOUT_SECONDS", 60.0)
    retries = _env_int("RIOTQUEENS_MODEL_MAX_RETRIES", 1)

    if provider_kind == "openai":
        base_url = _env("RIOTQUEENS_MODEL_BASE_URL")
        api_key = _env("RIOTQUEENS_MODEL_API_KEY")
        model_name = _env("RIOTQUEENS_MODEL_NAME", "riotqueens-chat-v1")
        if base_url and api_key:
            from app.domain.providers.openai_compatible import OpenAICompatibleProvider

            adapter = OpenAICompatibleProvider(
                base_url=base_url,
                api_key=api_key,
                model=model_name,
                timeout_seconds=timeout,
                omit_frequency_penalty=_env_bool("RIOTQUEENS_MODEL_OMIT_FREQUENCY_PENALTY"),
            )
            providers: Mapping[Route, ModelProvider] = {route: adapter for route in Route}
            fallback_providers: Mapping[Route, Sequence[ModelProvider]] = {}
            fallback_kind = _env("RIOTQUEENS_FALLBACK_MODEL_PROVIDER").strip().lower()
            fallback_base_url = _env("RIOTQUEENS_FALLBACK_MODEL_BASE_URL")
            fallback_api_key = _env("RIOTQUEENS_FALLBACK_MODEL_API_KEY")
            fallback_model = _env("RIOTQUEENS_FALLBACK_MODEL_NAME")
            if (
                fallback_kind == "openai"
                and fallback_base_url
                and fallback_api_key
                and fallback_model
            ):
                fallback_temperature = _env("RIOTQUEENS_FALLBACK_MODEL_TEMPERATURE").strip()
                fallback_freq = _env("RIOTQUEENS_FALLBACK_MODEL_FREQUENCY_PENALTY").strip()
                fallback_adapter = OpenAICompatibleProvider(
                    base_url=fallback_base_url,
                    api_key=fallback_api_key,
                    model=fallback_model,
                    timeout_seconds=timeout,
                    temperature=float(fallback_temperature) if fallback_temperature else None,
                    frequency_penalty=float(fallback_freq) if fallback_freq else None,
                    omit_frequency_penalty=_env_bool(
                        "RIOTQUEENS_FALLBACK_MODEL_OMIT_FREQUENCY_PENALTY"
                    ),
                )
                fallback_providers = {route: (fallback_adapter,) for route in Route}
            return ModelRouter(
                providers=providers,
                fallback_providers=fallback_providers,
                timeout_seconds=timeout,
                max_retries=retries,
            )

    return ModelRouter(timeout_seconds=timeout, max_retries=retries)


def runtime_status(router: ModelRouter) -> dict[str, object]:
    sample = router.providers.get(Route.FAST_CHAT)
    if sample is None:
        return {
            "provider": "unknown",
            "model": "unknown",
            "configured": False,
            "mode": "mock",
        }
    is_openai = getattr(sample, "name", "") == "openai-compatible"
    fallbacks = router.fallback_providers.get(Route.FAST_CHAT, ())
    return {
        "provider": sample.name,
        "model": sample.model,
        "configured": is_openai,
        "mode": "real" if is_openai else "mock",
        "timeout_seconds": router.timeout_seconds,
        "max_retries": router.max_retries,
        "fallback_configured": bool(fallbacks),
        "fallback_model": fallbacks[0].model if fallbacks else None,
    }
