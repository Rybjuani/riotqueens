"""OpenAI-compatible HTTP model provider adapter.

The adapter owns HTTP details and translates transport/upstream failures into
typed ProviderError exceptions. It never hides a provider outage as a
successful ModelResponse. Retry policy belongs to ModelRouter; HTTP mapping
belongs to FastAPI.

Public callers get sanitized errors. Owner Console root may request raw_errors
to attach a truncated upstream cartel (status + error object + body preview).
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.domain.contracts import ModelRequest, ModelResponse, Usage
from app.domain.providers.errors import (
    ProviderAuthError,
    ProviderConnectError,
    ProviderContentBlockedError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderUpstreamError,
)

_UPSTREAM_BODY_PREVIEW_LIMIT = 2_000


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def clamp_max_tokens(value: int) -> int:
    """Pickle §3 T1 cap: max_tokens 180–220."""
    return max(180, min(220, value))


def _preview_body(text: str) -> str:
    if len(text) <= _UPSTREAM_BODY_PREVIEW_LIMIT:
        return text
    return text[:_UPSTREAM_BODY_PREVIEW_LIMIT] + "…"


def build_upstream_cartel(response: httpx.Response) -> dict[str, Any]:
    """Build the Owner-visible OpenRouter/OpenAI error cartel (no secrets)."""
    body_text = response.text or ""
    cartel: dict[str, Any] = {
        "status": response.status_code,
        "body_preview": _preview_body(body_text),
    }
    try:
        data = response.json()
    except ValueError:
        return cartel
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            cartel["error"] = {
                key: error.get(key)
                for key in ("message", "code", "type", "reason", "status")
                if error.get(key) is not None
            }
        else:
            cartel["error"] = data.get("error")
    return cartel


def _upstream_message(cartel: dict[str, Any]) -> str:
    error = cartel.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    preview = cartel.get("body_preview")
    if isinstance(preview, str) and preview.strip():
        return preview.strip()[:240]
    status = cartel.get("status")
    return f"Upstream HTTP {status}" if status is not None else "Upstream error"


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
        temperature: float | None = None,
        frequency_penalty: float | None = None,
        omit_frequency_penalty: bool = False,
        max_tokens: int | None = None,
        clamp_tokens: bool = True,
        raw_errors: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = (
            temperature
            if temperature is not None
            else _env_float("RIOTQUEENS_MODEL_TEMPERATURE", 0.9)
        )
        configured = (
            max_tokens
            if max_tokens is not None
            else _env_int("RIOTQUEENS_MODEL_MAX_TOKENS", 200)
        )
        self.max_tokens = clamp_max_tokens(configured) if clamp_tokens else max(1, configured)
        self.clamp_tokens = clamp_tokens
        self.raw_errors = raw_errors
        self.frequency_penalty = (
            None
            if omit_frequency_penalty
            else (
                frequency_penalty
                if frequency_penalty is not None
                else _env_float("RIOTQUEENS_MODEL_FREQUENCY_PENALTY", 0.4)
            )
        )
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout_seconds,
            transport=transport,
        )

    def clone(
        self,
        *,
        model: str | None = None,
        temperature: float | None = None,
        frequency_penalty: float | None = None,
        max_tokens: int | None = None,
        clamp_tokens: bool | None = None,
        raw_errors: bool | None = None,
    ) -> OpenAICompatibleProvider:
        """Shallow clone sharing the same HTTP client (Owner Console overrides)."""
        clone = OpenAICompatibleProvider.__new__(OpenAICompatibleProvider)
        clone.base_url = self.base_url
        clone.model = model if model is not None else self.model
        clone.temperature = temperature if temperature is not None else self.temperature
        clone.clamp_tokens = self.clamp_tokens if clamp_tokens is None else clamp_tokens
        configured = max_tokens if max_tokens is not None else self.max_tokens
        clone.max_tokens = (
            clamp_max_tokens(configured) if clone.clamp_tokens else max(1, configured)
        )
        clone.frequency_penalty = (
            frequency_penalty if frequency_penalty is not None else self.frequency_penalty
        )
        clone.raw_errors = self.raw_errors if raw_errors is None else raw_errors
        clone._client = self._client
        return clone

    async def generate(self, request: ModelRequest) -> ModelResponse:
        payload = self._build_payload(request)
        try:
            response = await self._client.post("/chat/completions", json=payload)
        except httpx.TimeoutException:
            raise ProviderTimeoutError() from None
        except httpx.RequestError:
            raise ProviderConnectError() from None

        if self.raw_errors:
            return self._handle_raw(response)

        status = response.status_code
        if status == 400 and self._response_reports_content_block(response):
            raise ProviderContentBlockedError() from None
        if status in (401, 403):
            raise ProviderAuthError() from None
        if status == 429:
            raise ProviderRateLimitError() from None
        if status >= 500:
            raise ProviderServerError() from None
        if 400 <= status < 500:
            raise ProviderRequestError() from None
        if status < 200 or status >= 300:
            raise ProviderInvalidResponseError() from None

        try:
            data = response.json()
        except ValueError:
            raise ProviderInvalidResponseError() from None
        if not isinstance(data, dict):
            raise ProviderInvalidResponseError() from None
        if self._payload_reports_content_block(data):
            raise ProviderContentBlockedError() from None

        content = self._extract_content(data)
        if not content:
            raise ProviderInvalidResponseError() from None

        return ModelResponse(
            provider=self.name,
            model=self.model,
            content=content,
            usage=self._extract_usage(data),
            finish_reason=self._extract_finish_reason(data),
        )

    def _handle_raw(self, response: httpx.Response) -> ModelResponse:
        status = response.status_code
        if status < 200 or status >= 300:
            cartel = build_upstream_cartel(response)
            blocked = self._response_reports_content_block(response)
            raise ProviderUpstreamError(
                message=_upstream_message(cartel),
                upstream=cartel,
                blocked=blocked,
            ) from None

        try:
            data = response.json()
        except ValueError:
            cartel = build_upstream_cartel(response)
            raise ProviderUpstreamError(
                message="Upstream returned non-JSON body",
                upstream=cartel,
            ) from None
        if not isinstance(data, dict):
            raise ProviderUpstreamError(
                message="Upstream returned a non-object JSON body",
                upstream={"status": status, "body_preview": _preview_body(response.text or "")},
            ) from None

        if self._payload_reports_content_block(data):
            blocked_meta = (
                data.get("error")
                or data.get("promptFeedback")
                or data.get("prompt_feedback")
            )
            cartel = {
                "status": status,
                "error": blocked_meta,
                "body_preview": _preview_body(json.dumps(data, ensure_ascii=False)),
            }
            raise ProviderUpstreamError(
                message=_upstream_message(cartel),
                upstream=cartel,
                blocked=True,
            ) from None

        content = self._extract_content(data)
        if not content:
            cartel = {
                "status": status,
                "error": data.get("error"),
                "body_preview": _preview_body(json.dumps(data, ensure_ascii=False)),
            }
            raise ProviderUpstreamError(
                message="Upstream returned empty assistant content",
                upstream=cartel,
            ) from None

        return ModelResponse(
            provider=self.name,
            model=self.model,
            content=content,
            usage=self._extract_usage(data),
            finish_reason=self._extract_finish_reason(data),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _build_payload(self, request: ModelRequest) -> dict[str, Any]:
        # Higher temperature + mild frequency_penalty reduce "corporate assistant"
        # default wording; overridable via RIOTQUEENS_MODEL_* env.
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content} for message in request.messages
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if self.frequency_penalty is not None:
            payload["frequency_penalty"] = self.frequency_penalty
        return payload

    def _extract_content(self, data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        return content.strip() if isinstance(content, str) else ""

    def _extract_finish_reason(self, data: dict[str, Any]) -> str | None:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        reason = first.get("finish_reason") or first.get("finishReason")
        return reason if isinstance(reason, str) else None

    def _extract_usage(self, data: dict[str, Any]) -> Usage:
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return Usage()
        try:
            return Usage(
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
            )
        except (TypeError, ValueError):
            return Usage()

    def _response_reports_content_block(self, response: httpx.Response) -> bool:
        try:
            data = response.json()
        except ValueError:
            return False
        return isinstance(data, dict) and self._payload_reports_content_block(data)

    @staticmethod
    def _payload_reports_content_block(data: dict[str, Any]) -> bool:
        blocked_reasons = {
            "BLOCKED",
            "BLOCKLIST",
            "CONTENT_FILTER",
            "PROHIBITED_CONTENT",
            "SAFETY",
        }

        prompt_feedback = data.get("promptFeedback") or data.get("prompt_feedback")
        if isinstance(prompt_feedback, dict):
            reason = prompt_feedback.get("blockReason") or prompt_feedback.get("block_reason")
            if isinstance(reason, str) and reason.upper() in blocked_reasons:
                return True

        choices = data.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                reason = choice.get("finish_reason") or choice.get("finishReason")
                if isinstance(reason, str) and reason.upper() in blocked_reasons:
                    return True

        error = data.get("error")
        if isinstance(error, dict):
            reason = error.get("reason") or error.get("status")
            if isinstance(reason, str) and reason.upper() in blocked_reasons:
                return True
            message = error.get("message")
            if isinstance(message, str):
                lowered = message.lower()
                if "content" in lowered and "filter" in lowered:
                    return True
        return False
