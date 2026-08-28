"""Owner Console gate — Auth0 sub allowlist (prod) or user_id allowlist (auth off)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request, status

from .authorization import Principal
from .identity import (
    IdentityConfigurationError,
    IdentityVerificationError,
    auth_is_required,
    build_auth0_verifier,
    require_principal,
)


def _csv_set(name: str) -> set[str]:
    raw = os.environ.get(name, "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def owner_auth0_subjects() -> set[str]:
    return _csv_set("RIOTQUEENS_OWNER_AUTH0_SUBJECTS")


def owner_user_ids() -> set[str]:
    return _csv_set("RIOTQUEENS_OWNER_USER_IDS")


def owner_console_configured() -> bool:
    if auth_is_required():
        return bool(owner_auth0_subjects())
    return bool(owner_user_ids())


@dataclass
class OwnerContext:
    """Resolved Owner actor for console routes."""

    principal: Principal | None
    user_id: str
    auth0_subject: str | None = None


@dataclass
class RollbackTrace:
    attempted: bool = False
    succeeded: bool | None = None


@dataclass
class MemoryTrace:
    lost: bool = False
    detail: str | None = None


@dataclass
class LocalGuardTrace:
    triggered: bool = False
    reason: str | None = None
    bypass: bool = False


@dataclass
class FallbackTrace:
    configured: bool = False
    used: bool = False
    model: str | None = None


@dataclass
class RewriteTrace:
    applied: bool = False
    ops: list[str] = field(default_factory=list)


@dataclass
class OwnerTrace:
    channel: str
    system: str
    history_messages: int = 0
    max_turns: int = 0
    truncated: bool = False
    max_tokens: int | None = None
    temperature: float | None = None
    provider: str | None = None
    model: str | None = None
    local_guard: LocalGuardTrace = field(default_factory=LocalGuardTrace)
    fallback: FallbackTrace = field(default_factory=FallbackTrace)
    rewrite: RewriteTrace = field(default_factory=RewriteTrace)
    latency_ms: int = 0
    retry_count: int = 0
    rollback: RollbackTrace = field(default_factory=RollbackTrace)
    memory: MemoryTrace = field(default_factory=MemoryTrace)
    blocked: bool = False
    finish_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "system": self.system,
            "history_messages": self.history_messages,
            "max_turns": self.max_turns,
            "truncated": self.truncated,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "provider": self.provider,
            "model": self.model,
            "local_guard": {
                "triggered": self.local_guard.triggered,
                "reason": self.local_guard.reason,
                "bypass": self.local_guard.bypass,
            },
            "fallback": {
                "configured": self.fallback.configured,
                "used": self.fallback.used,
                "model": self.fallback.model,
            },
            "rewrite": {
                "applied": self.rewrite.applied,
                "ops": list(self.rewrite.ops),
            },
            "latency_ms": self.latency_ms,
            "retry_count": self.retry_count,
            "rollback": {
                "attempted": self.rollback.attempted,
                "succeeded": self.rollback.succeeded,
            },
            "memory": {
                "lost": self.memory.lost,
                "detail": self.memory.detail,
            },
            "blocked": self.blocked,
            "finish_reason": self.finish_reason,
        }


def _extract_bearer(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def require_owner(
    request: Request,
    *,
    body_user_id: str | None,
) -> OwnerContext:
    """Fail-closed Owner gate for /v1/usuario, /v1/root, /v1/compare."""

    if auth_is_required():
        allowed = owner_auth0_subjects()
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "owner_forbidden",
                    "message": "Owner console is not configured.",
                },
            )
        token = _extract_bearer(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )
        try:
            verifier = getattr(request.app.state, "auth0_verifier", None) or build_auth0_verifier()
            external = verifier.verify(token)
            if external.subject not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "owner_forbidden",
                        "message": "Owner allowlist rejected this subject.",
                    },
                )
            repository = getattr(request.app.state, "identity_repository", None)
            if repository is None:
                raise IdentityConfigurationError("RiotQueens identity repository is unavailable")
            principal = await repository.resolve(external)
        except HTTPException:
            raise
        except IdentityConfigurationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity unavailable",
            ) from None
        except IdentityVerificationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            ) from None
        return OwnerContext(
            principal=principal,
            user_id=principal.user_id,
            auth0_subject=external.subject,
        )

    allowed_users = owner_user_ids()
    if not allowed_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "owner_forbidden",
                "message": "Owner console is not configured.",
            },
        )
    if body_user_id is None or body_user_id not in allowed_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "owner_forbidden",
                "message": "Owner allowlist rejected this user_id.",
            },
        )
    # Still run require_principal for consistency (returns None when auth off).
    principal = await require_principal(request)
    return OwnerContext(principal=principal, user_id=body_user_id, auth0_subject=None)
