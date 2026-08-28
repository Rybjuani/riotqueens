"""Typed, sanitized model-provider errors.

Provider adapters raise these errors instead of converting transport/upstream
failures into successful-looking ModelResponse objects. The router owns retry
policy and the FastAPI layer owns HTTP mapping.

Errors intentionally carry only stable safe codes/messages. Never attach raw
upstream bodies, URLs, headers, credentials, or stack details.
"""

from __future__ import annotations


class ProviderError(Exception):
    code = "provider_error"
    safe_message = "Model provider error."
    retryable = False

    def __init__(self) -> None:
        super().__init__(self.code)

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
