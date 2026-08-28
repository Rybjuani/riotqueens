"""Clickwrap package helpers (ADR 0004)."""

from app.domain.authorization import AcceptanceSnapshot
from app.domain.consent import (
    current_acceptance_requirement,
    document_digest,
    snapshot_matches_required,
)


def test_document_digest_is_stable() -> None:
    a = document_digest(
        age_gate_version="2026-08-09",
        terms_version="2026-08-09",
        privacy_version="2026-08-09",
    )
    b = document_digest(
        age_gate_version="2026-08-09",
        terms_version="2026-08-09",
        privacy_version="2026-08-09",
    )
    assert a == b
    assert len(a) == 64


def test_snapshot_matches_required_versions() -> None:
    req = current_acceptance_requirement()
    good = AcceptanceSnapshot(
        age_confirmed=True,
        age_gate_version=req.age_gate_version,
        terms_version=req.terms_version,
        privacy_version=req.privacy_version,
    )
    assert snapshot_matches_required(good, req)
    stale = AcceptanceSnapshot(
        age_confirmed=True,
        age_gate_version="1970-01-01",
        terms_version=req.terms_version,
        privacy_version=req.privacy_version,
    )
    assert not snapshot_matches_required(stale, req)
    assert not snapshot_matches_required(None, req)
