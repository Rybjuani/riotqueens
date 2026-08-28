from app.domain.authorization import (
    AcceptanceRequirement,
    AcceptanceSnapshot,
    AuthorizationCode,
    Principal,
    ServiceTier,
    authorize_media_intent,
)
from app.domain.contracts import MediaIntent, MediaType


def _intent() -> MediaIntent:
    return MediaIntent(
        user_id="user-1",
        character_id="bardera",
        conversation_id="conversation-1",
        media_type=MediaType.SELFIE,
    )


def _acceptance() -> AcceptanceRequirement:
    return AcceptanceRequirement(
        age_gate_version="age-2026-08",
        terms_version="terms-2026-08",
        privacy_version="privacy-2026-08",
    )


def _principal(tier: ServiceTier = ServiceTier.T2) -> Principal:
    return Principal(
        user_id="user-1",
        tier=tier,
        acceptance=AcceptanceSnapshot(
            age_confirmed=True,
            age_gate_version="age-2026-08",
            terms_version="terms-2026-08",
            privacy_version="privacy-2026-08",
        ),
    )


def test_media_authorization_allows_matching_authenticated_tier() -> None:
    decision = authorize_media_intent(
        _intent(), _principal(), minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.allowed
    assert decision.code is AuthorizationCode.ALLOWED


def test_media_authorization_denies_missing_identity() -> None:
    decision = authorize_media_intent(
        _intent(), None, minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.code is AuthorizationCode.UNAUTHENTICATED


def test_media_authorization_denies_scope_mismatch() -> None:
    principal = Principal("different-user", ServiceTier.T3, _principal().acceptance)
    decision = authorize_media_intent(
        _intent(), principal, minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.code is AuthorizationCode.SCOPE_MISMATCH


def test_media_authorization_denies_stale_acceptance() -> None:
    principal = Principal(
        "user-1",
        ServiceTier.T3,
        AcceptanceSnapshot(True, "age-old", "terms-2026-08", "privacy-2026-08"),
    )
    decision = authorize_media_intent(
        _intent(), principal, minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.code is AuthorizationCode.ACCEPTANCE_REQUIRED


def test_media_authorization_denies_insufficient_tier() -> None:
    decision = authorize_media_intent(
        _intent(), _principal(ServiceTier.T1), minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.code is AuthorizationCode.ENTITLEMENT_REQUIRED


def test_media_authorization_fails_closed_when_acceptance_missing() -> None:
    principal = Principal("user-1", ServiceTier.T3, None)
    decision = authorize_media_intent(
        _intent(), principal, minimum_tier=ServiceTier.T2, acceptance=_acceptance()
    )

    assert decision.code is AuthorizationCode.ACCEPTANCE_REQUIRED
