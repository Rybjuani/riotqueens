"""Auth principal + acceptance snapshot (no media entitlement layer)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ServiceTier(IntEnum):
    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3


@dataclass(frozen=True)
class AcceptanceSnapshot:
    age_confirmed: bool
    age_gate_version: str
    terms_version: str
    privacy_version: str


@dataclass(frozen=True)
class AcceptanceRequirement:
    age_gate_version: str
    terms_version: str
    privacy_version: str


@dataclass(frozen=True)
class Principal:
    user_id: str
    tier: ServiceTier
    acceptance: AcceptanceSnapshot | None


__all__ = [
    "AcceptanceRequirement",
    "AcceptanceSnapshot",
    "Principal",
    "ServiceTier",
]
