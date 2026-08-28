"""Typed model-provider errors.

Provider adapters raise these errors instead of converting transport/upstream
failures into successful-looking ModelResponse objects. The router owns retry
policy and the FastAPI layer owns HTTP mapping.

Public chat handlers must only expose ``code`` / ``safe_message``.
Owner Console root may attach a truncated ``upstream`` cartel for diagnosis.
"""

from __future__ import annotations

from typing import Any


class ProviderError(Exception):
    code = "provider_error"
    safe_message = "Model provider error."
    retryable = False

    def __init__(self, *, upstream: dict[str, Any] | None = None) -> None:
        super().__init__(self.code)
        self.upstream = upstream

    def __str__(self) -> str:
        return self.code


class ProviderRetryableError(ProviderError):
    code = "provider_unavailable"
    safe_message = "Model provider temporarily unavailable."
    retryable = True


class ProviderNonRetryableError(ProviderError):
    code = "provider_config_error"
    safe_message = "Model provider is not available."
    retryable = False


class ProviderTimeoutError(ProviderRetryableError):
    code = "provider_timeout"
    safe_message = "Model provider timed out."


class ProviderConnectError(ProviderRetryableError):
    code = "provider_connect_failed"


class ProviderRateLimitError(ProviderRetryableError):
    code = "provider_rate_limited"


class ProviderServerError(ProviderRetryableError):
    code = "provider_server_error"


class ProviderInvalidResponseError(ProviderRetryableError):
    code = "provider_invalid_response"
    safe_message = "Model provider returned an invalid response."


class ProviderAuthError(ProviderNonRetryableError):
    code = "provider_config_error"


class ProviderRequestError(ProviderNonRetryableError):
    code = "provider_config_error"


class ProviderContentBlockedError(ProviderNonRetryableError):
    """The upstream explicitly withheld a response for content-policy reasons."""

    code = "provider_content_blocked"
    safe_message = "Model provider withheld the response."


class ProviderUpstreamError(ProviderNonRetryableError):
    """Owner Console root: honest upstream failure with raw cartel attached."""

    code = "upstream_error"
    safe_message = "Upstream model provider returned an error."

    def __init__(
        self,
        *,
        message: str | None = None,
        upstream: dict[str, Any] | None = None,
        blocked: bool = False,
    ) -> None:
        super().__init__(upstream=upstream)
        if message:
            self.safe_message = message
        self.blocked = blocked
