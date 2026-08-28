"""Server-owned authentication and entitlement policy primitives.

This module deliberately does not implement login, sessions, payments or a
legal jurisdiction. An eventual auth adapter must construct ``Principal``
from a verified identity; media handlers then call ``authorize_media_intent``
before selecting assets or issuing storage URLs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from .contracts import MediaIntent


class ServiceTier(IntEnum):
    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3


class AuthorizationCode(StrEnum):
    ALLOWED = "allowed"
    UNAUTHENTICATED = "unauthenticated"
    SCOPE_MISMATCH = "scope_mismatch"
    ACCEPTANCE_REQUIRED = "acceptance_required"
    ENTITLEMENT_REQUIRED = "entitlement_required"


@dataclass(frozen=True)
class AcceptanceSnapshot:
    """Versions actually accepted by the authenticated principal."""

    age_confirmed: bool
    age_gate_version: str
    terms_version: str
    privacy_version: str


@dataclass(frozen=True)
class AcceptanceRequirement:
    """Server-selected versions required for a protected operation."""

    age_gate_version: str
    terms_version: str
    privacy_version: str


@dataclass(frozen=True)
class Principal:
    """Identity and service state produced by a future auth adapter."""

    user_id: str
    tier: ServiceTier
    acceptance: AcceptanceSnapshot | None


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    code: AuthorizationCode


def _acceptance_matches(
    snapshot: AcceptanceSnapshot | None,
    required: AcceptanceRequirement,
) -> bool:
    return bool(
        snapshot
        and snapshot.age_confirmed
        and snapshot.age_gate_version == required.age_gate_version
        and snapshot.terms_version == required.terms_version
        and snapshot.privacy_version == required.privacy_version
    )


def authorize_media_intent(
    intent: MediaIntent,
    principal: Principal | None,
    *,
    minimum_tier: ServiceTier,
    acceptance: AcceptanceRequirement,
) -> AuthorizationDecision:
    """Fail closed before media selection, storage or delivery."""

    if principal is None:
        return AuthorizationDecision(False, AuthorizationCode.UNAUTHENTICATED)
    if principal.user_id != intent.user_id:
        return AuthorizationDecision(False, AuthorizationCode.SCOPE_MISMATCH)
    if not _acceptance_matches(principal.acceptance, acceptance):
        return AuthorizationDecision(False, AuthorizationCode.ACCEPTANCE_REQUIRED)
    if principal.tier < minimum_tier:
        return AuthorizationDecision(False, AuthorizationCode.ENTITLEMENT_REQUIRED)
    return AuthorizationDecision(True, AuthorizationCode.ALLOWED)


__all__ = [
    "AcceptanceRequirement",
    "AcceptanceSnapshot",
    "AuthorizationCode",
    "AuthorizationDecision",
    "Principal",
    "ServiceTier",
    "authorize_media_intent",
]
