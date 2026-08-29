"""Auth0 token verification and RiotQueens-owned identity bindings.

The Auth0 subject is deliberately an external credential, never a domain
primary key.  The repository boundary makes the binding replaceable and lets
the API resolve the durable RiotQueens UUID before a request reaches domain
logic.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from uuid import uuid4

import asyncpg
import jwt
from fastapi import HTTPException, Request, status

from .authorization import Principal, ServiceTier


class IdentityConfigurationError(RuntimeError):
    """Raised when a protected runtime has no complete IAM configuration."""


class IdentityVerificationError(RuntimeError):
    """Raised for an untrusted, malformed, expired, or mismatched token."""


@dataclass(frozen=True)
class VerifiedExternalIdentity:
    provider: str
    subject: str


class InMemoryIdentityRepository:
    """Deterministic repository for tests only; production uses PostgreSQL."""

    def __init__(self) -> None:
        self._bindings: dict[tuple[str, str], str] = {}
        self._lock = asyncio.Lock()

    async def resolve(self, identity: VerifiedExternalIdentity) -> Principal:
        key = (identity.provider, identity.subject)
        async with self._lock:
            user_id = self._bindings.setdefault(key, str(uuid4()))
        # IAM creates no product entitlement, tier or legal acceptance.
        return Principal(user_id=user_id, tier=ServiceTier.T0, acceptance=None)


class PostgresIdentityRepository:
    """Transactional PostgreSQL implementation of the external identity map."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        *,
        consent_repository: object | None = None,
    ) -> None:
        self._pool = pool
        # Optional PostgresConsentRepository; typed loosely to avoid a cycle.
        self._consent_repository = consent_repository

    @staticmethod
    async def _active_tier(connection: asyncpg.Connection, user_id: object) -> ServiceTier:
        """Resolve a server-owned active entitlement; users default to T0."""
        value = await connection.fetchval(
            """
            SELECT tier FROM user_tier_entitlements
            WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY granted_at DESC
            LIMIT 1
            """,
            user_id,
        )
        try:
            return ServiceTier(int(value)) if value is not None else ServiceTier.T0
        except (TypeError, ValueError):
            return ServiceTier.T0

    async def resolve(self, identity: VerifiedExternalIdentity) -> Principal:
        async with self._pool.acquire() as connection, connection.transaction():
            existing = await connection.fetchval(
                """
                SELECT user_id FROM external_identities
                WHERE provider = $1 AND provider_subject = $2
                FOR UPDATE
                """,
                identity.provider,
                identity.subject,
            )
            if existing is None:
                user_id = uuid4()
                await connection.execute("INSERT INTO users (id) VALUES ($1)", user_id)
                try:
                    await connection.execute(
                        """
                        INSERT INTO external_identities (user_id, provider, provider_subject)
                        VALUES ($1, $2, $3)
                        """,
                        user_id,
                        identity.provider,
                        identity.subject,
                    )
                except asyncpg.UniqueViolationError:
                    # A concurrent first login won; use its durable binding.
                    existing = await connection.fetchval(
                        """
                        SELECT user_id FROM external_identities
                        WHERE provider = $1 AND provider_subject = $2
                        """,
                        identity.provider,
                        identity.subject,
                    )
                    if existing is None:
                        raise
                    user_id = existing
            else:
                user_id = existing
            tier = await self._active_tier(connection, user_id)
        acceptance = None
        if self._consent_repository is not None:
            acceptance = await self._consent_repository.latest_for_user(str(user_id))
        return Principal(
            user_id=str(user_id),
            tier=tier,
            acceptance=acceptance,
        )


class Auth0JWTVerifier:
    """Validate RS256 access tokens with PyJWT's maintained JWKS client."""

    def __init__(self, *, issuer: str, audience: str, jwks_url: str) -> None:
        if not issuer or not audience or not jwks_url:
            raise IdentityConfigurationError("Auth0 issuer, audience and JWKS URL are required")
        self._issuer = issuer.rstrip("/") + "/"
        self._audience = audience
        self._jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True)

    def verify(self, token: str) -> VerifiedExternalIdentity:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise IdentityVerificationError("Access token is not valid") from exc
        except Exception as exc:  # JWKS transport/key failures are never trusted.
            raise IdentityVerificationError("Access token cannot be verified") from exc
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise IdentityVerificationError("Access token has no subject")
        return VerifiedExternalIdentity(provider="auth0", subject=subject)


def auth_is_required() -> bool:
    return os.environ.get("RIOTQUEENS_AUTH_ENABLED", "true").lower() == "true"


def build_auth0_verifier() -> Auth0JWTVerifier:
    return Auth0JWTVerifier(
        issuer=os.environ.get("RIOTQUEENS_AUTH0_ISSUER", ""),
        audience=os.environ.get("RIOTQUEENS_AUTH0_AUDIENCE", ""),
        jwks_url=os.environ.get("RIOTQUEENS_AUTH0_JWKS_URL", ""),
    )


async def require_principal(request: Request) -> Principal | None:
    """Resolve the authenticated actor or fail closed before domain handlers.

    ``RIOTQUEENS_AUTH_ENABLED=false`` exists only for the pre-auth test
    fixture while legacy in-process behavior is migrated. It is never a
    deploy default: production defaults to required authentication.
    """

    if not auth_is_required():
        return None
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        verifier = getattr(request.app.state, "auth0_verifier", None) or build_auth0_verifier()
        external_identity = verifier.verify(token)
        repository = getattr(request.app.state, "identity_repository", None)
        if repository is None:
            raise IdentityConfigurationError("RiotQueens identity repository is unavailable")
        return await repository.resolve(external_identity)
    except IdentityConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity unavailable",
        )
    except IdentityVerificationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
