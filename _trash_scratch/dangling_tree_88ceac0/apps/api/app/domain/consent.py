"""Versioned clickwrap acceptance (ADR 0004).

The client sends only confirmations and the versions it was shown.
The server stamps identity, UTC time and a digest of those versions.
Marketing / notification consent is intentionally out of scope here.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg

from .authorization import AcceptanceRequirement, AcceptanceSnapshot

# Baseline legal package for the free/preview cut. Bump together when
# material terms or privacy text change; a mismatch forces re-acceptance.
DEFAULT_AGE_GATE_VERSION = "2026-08-09"
DEFAULT_TERMS_VERSION = "2026-08-09"
DEFAULT_PRIVACY_VERSION = "2026-08-09"


def _env_version(name: str, default: str) -> str:
    raw = os.environ.get(name, "").strip()
    return raw or default


def current_acceptance_requirement() -> AcceptanceRequirement:
    return AcceptanceRequirement(
        age_gate_version=_env_version(
            "RIOTQUEENS_AGE_GATE_VERSION", DEFAULT_AGE_GATE_VERSION
        ),
        terms_version=_env_version("RIOTQUEENS_TERMS_VERSION", DEFAULT_TERMS_VERSION),
        privacy_version=_env_version(
            "RIOTQUEENS_PRIVACY_VERSION", DEFAULT_PRIVACY_VERSION
        ),
    )


def document_digest(
    *,
    age_gate_version: str,
    terms_version: str,
    privacy_version: str,
) -> str:
    """Stable digest of the exact version triple accepted."""

    payload = f"age={age_gate_version}|terms={terms_version}|privacy={privacy_version}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AcceptanceRecord:
    acceptance_id: str
    user_id: str
    age_confirmed: bool
    age_gate_version: str
    terms_version: str
    privacy_version: str
    document_digest: str
    accepted_at: datetime


def snapshot_matches_required(
    snapshot: AcceptanceSnapshot | None,
    required: AcceptanceRequirement | None = None,
) -> bool:
    req = required or current_acceptance_requirement()
    return bool(
        snapshot
        and snapshot.age_confirmed
        and snapshot.age_gate_version == req.age_gate_version
        and snapshot.terms_version == req.terms_version
        and snapshot.privacy_version == req.privacy_version
    )


class PostgresConsentRepository:
    """Append-only acceptance store bound to durable users.id."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def latest_for_user(self, user_id: str) -> AcceptanceSnapshot | None:
        try:
            uid = UUID(user_id)
        except ValueError:
            return None
        row = await self._pool.fetchrow(
            """
            SELECT age_confirmed, age_gate_version, terms_version, privacy_version
            FROM consent_acceptances
            WHERE user_id = $1
            ORDER BY accepted_at DESC
            LIMIT 1
            """,
            uid,
        )
        if row is None:
            return None
        return AcceptanceSnapshot(
            age_confirmed=bool(row["age_confirmed"]),
            age_gate_version=row["age_gate_version"],
            terms_version=row["terms_version"],
            privacy_version=row["privacy_version"],
        )

    async def record(
        self,
        *,
        user_id: str,
        age_confirmed: bool,
        age_gate_version: str,
        terms_version: str,
        privacy_version: str,
    ) -> AcceptanceRecord:
        if not age_confirmed:
            raise ValueError("age_confirmed must be true")
        required = current_acceptance_requirement()
        if (
            age_gate_version != required.age_gate_version
            or terms_version != required.terms_version
            or privacy_version != required.privacy_version
        ):
            raise ValueError("presented versions do not match current package")

        uid = UUID(user_id)
        acceptance_id = uuid4()
        digest = document_digest(
            age_gate_version=age_gate_version,
            terms_version=terms_version,
            privacy_version=privacy_version,
        )
        accepted_at = datetime.now(UTC)
        await self._pool.execute(
            """
            INSERT INTO consent_acceptances (
              acceptance_id, user_id, age_confirmed,
              age_gate_version, terms_version, privacy_version,
              document_digest, accepted_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            acceptance_id,
            uid,
            True,
            age_gate_version,
            terms_version,
            privacy_version,
            digest,
            accepted_at,
        )
        return AcceptanceRecord(
            acceptance_id=str(acceptance_id),
            user_id=user_id,
            age_confirmed=True,
            age_gate_version=age_gate_version,
            terms_version=terms_version,
            privacy_version=privacy_version,
            document_digest=digest,
            accepted_at=accepted_at,
        )


__all__ = [
    "AcceptanceRecord",
    "DEFAULT_AGE_GATE_VERSION",
    "DEFAULT_PRIVACY_VERSION",
    "DEFAULT_TERMS_VERSION",
    "PostgresConsentRepository",
    "current_acceptance_requirement",
    "document_digest",
    "snapshot_matches_required",
]
