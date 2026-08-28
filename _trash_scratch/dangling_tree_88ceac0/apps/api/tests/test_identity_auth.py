"""C3 authentication regressions; all use local keys and fake Auth0 adapters."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.domain.authorization import AcceptanceSnapshot, Principal, ServiceTier
from app.domain.consent import current_acceptance_requirement
from app.domain.identity import (
    Auth0JWTVerifier,
    IdentityVerificationError,
    InMemoryIdentityRepository,
    VerifiedExternalIdentity,
)


class _SigningKey:
    def __init__(self, key) -> None:
        self.key = key


class _LocalJwks:
    def __init__(self, key) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, _token: str) -> _SigningKey:
        return _SigningKey(self._key)


def _token(
    private_key,
    *,
    sub: str = "auth0|alice",
    issuer: str = "https://tenant.ca.auth0.com/",
    audience: str = "https://api.riotqueens.ai",
    expires_in: int = 300,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": sub,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        },
        private_key,
        algorithm="RS256",
    )


def test_auth0_verifier_rejects_wrong_issuer_audience_and_expiry() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = Auth0JWTVerifier(
        issuer="https://tenant.ca.auth0.com/",
        audience="https://api.riotqueens.ai",
        jwks_url="https://tenant.ca.auth0.com/.well-known/jwks.json",
    )
    verifier._jwks_client = _LocalJwks(private_key.public_key())  # local JWKS fixture
    assert verifier.verify(_token(private_key)).subject == "auth0|alice"
    for token in (
        _token(private_key, issuer="https://other.ca.auth0.com/"),
        _token(private_key, audience="https://other-api"),
        _token(private_key, expires_in=-1),
    ):
        with pytest.raises(IdentityVerificationError):
            verifier.verify(token)


@pytest.mark.asyncio
async def test_same_external_subject_resolves_same_internal_uuid() -> None:
    repository = InMemoryIdentityRepository()
    first = await repository.resolve(VerifiedExternalIdentity("auth0", "auth0|same"))
    second = await repository.resolve(VerifiedExternalIdentity("auth0", "auth0|same"))
    other = await repository.resolve(VerifiedExternalIdentity("auth0", "auth0|other"))
    assert first.user_id == second.user_id
    assert first.user_id != other.user_id
    assert first.tier.value == 0 and first.acceptance is None


@pytest.mark.asyncio
async def test_protected_api_fails_closed_and_ignores_forged_browser_user_id(monkeypatch) -> None:
    monkeypatch.setenv("RIOTQUEENS_AUTH_ENABLED", "true")
    import app.main as main_mod

    importlib.reload(main_mod)

    class Verifier:
        def verify(self, token: str) -> VerifiedExternalIdentity:
            if token != "valid":
                raise IdentityVerificationError("invalid")
            return VerifiedExternalIdentity("auth0", "auth0|alice")

    main_mod.app.state.auth0_verifier = Verifier()
    base_repo = InMemoryIdentityRepository()
    required = current_acceptance_requirement()

    class AcceptedRepo:
        async def resolve(self, identity: VerifiedExternalIdentity) -> Principal:
            principal = await base_repo.resolve(identity)
            return Principal(
                user_id=principal.user_id,
                tier=ServiceTier.T0,
                acceptance=AcceptanceSnapshot(
                    age_confirmed=True,
                    age_gate_version=required.age_gate_version,
                    terms_version=required.terms_version,
                    privacy_version=required.privacy_version,
                ),
            )

    main_mod.app.state.identity_repository = InMemoryIdentityRepository()
    transport = httpx.ASGITransport(app=main_mod.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "hola", "character_id": "bardera", "conversation_id": "c1"}
        no_token = await client.post("/v1/chat", json=payload)
        invalid = await client.post(
            "/v1/chat", headers={"Authorization": "Bearer bad"}, json=payload
        )
        needs_accept = await client.post(
            "/v1/chat",
            headers={"Authorization": "Bearer valid"},
            json={**payload, "user_id": "victim-user"},
        )
        main_mod.app.state.identity_repository = AcceptedRepo()
        forged = await client.post(
            "/v1/chat",
            headers={"Authorization": "Bearer valid"},
            json={**payload, "user_id": "victim-user"},
        )
    assert no_token.status_code == 401
    assert invalid.status_code == 401
    assert needs_accept.status_code == 403
    assert needs_accept.json()["detail"]["code"] == "acceptance_required"
    assert forged.status_code == 200
    record = next(iter(main_mod.conversation_store._records.values()))
    assert record.user_id != "victim-user"
