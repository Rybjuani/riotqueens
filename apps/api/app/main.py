"""RiotQueens API — nuclear rebuild: chat + auth + consent + conversations. No cape."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .domain.authorization import Principal
from .domain.consent import (
    PostgresConsentRepository,
    current_acceptance_requirement,
    snapshot_matches_required,
)
from .domain.context import assemble_request_messages, build_model_request
from .domain.contracts import (
    ChatAssistantResponse,
    ChatRequest,
    ChatResponse,
    ConsentAcceptRequest,
    ConsentAcceptResponse,
    ConsentStatusResponse,
    ConversationDeleteResponse,
    ConversationMessageView,
    ConversationScopeRequest,
    ConversationSummary,
    QueenIdentifier,
    ScopeIdentifier,
)
from .domain.conversations import (
    ConversationScopeKey,
    InProcessConversationStore,
    PostgresConversationStore,
)
from .domain.identity import (
    PostgresIdentityRepository,
    auth_is_required,
    require_principal,
)
from .domain.providers.errors import (
    ProviderAuthError,
    ProviderConnectError,
    ProviderContentBlockedError,
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
    ProviderTimeoutError,
)
from .domain.queens import is_registered_queen
from .domain.router import build_router, runtime_status


def _env_int_optional(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


_CONVERSATION_MAX_TURNS = _env_int_optional("RIOTQUEENS_CONVERSATION_MAX_TURNS", 8)

conversation_store: InProcessConversationStore | PostgresConversationStore = (
    InProcessConversationStore(max_turns=_CONVERSATION_MAX_TURNS)
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conversation_store
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        import asyncpg

        dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        pool = await asyncpg.create_pool(dsn)
        app.state.db_pool = pool
        consent_repo = PostgresConsentRepository(pool)
        app.state.consent_repository = consent_repo
        app.state.identity_repository = PostgresIdentityRepository(
            pool, consent_repository=consent_repo
        )
        conversation_store = PostgresConversationStore(
            pool, max_turns=_CONVERSATION_MAX_TURNS
        )
    yield
    pool = getattr(app.state, "db_pool", None)
    if pool is not None:
        await pool.close()


app = FastAPI(title="RiotQueens API", version="0.5.0-nuclear", lifespan=lifespan)


class NoStoreV1Middleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope.get("path", "").startswith("/v1/"):
            await self.app(scope, receive, send)
            return

        async def send_no_store(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, send_no_store)


_cors_env = os.environ.get("RIOTQUEENS_CORS_ORIGINS", "http://localhost:3000")
_cors_origins = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(NoStoreV1Middleware)

router = build_router()


def _require_registered_queen(character_id: str) -> None:
    if not is_registered_queen(character_id):
        raise HTTPException(
            status_code=404,
            detail={"code": "queen_not_found", "message": "Queen is not available."},
        )


def _actor_user_id(principal: Principal | None, browser_user_id: str | None) -> str:
    if auth_is_required():
        if principal is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return principal.user_id
    if browser_user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return browser_user_id


def _require_current_acceptance(principal: Principal | None) -> None:
    if not auth_is_required():
        return
    if principal is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not snapshot_matches_required(principal.acceptance):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "acceptance_required",
                "message": "Current age gate and legal acceptance are required.",
            },
        )


_PROVIDER_HTTP_STATUS: dict[type[ProviderError], int] = {
    ProviderTimeoutError: 504,
    ProviderInvalidResponseError: 502,
    ProviderConnectError: 503,
    ProviderRateLimitError: 503,
    ProviderServerError: 503,
    ProviderAuthError: 503,
    ProviderRequestError: 503,
    ProviderContentBlockedError: 502,
}


@app.exception_handler(ProviderError)
async def provider_error_handler(_request: Request, exc: ProviderError) -> JSONResponse:
    status_code = 503
    for error_type, mapped_status in _PROVIDER_HTTP_STATUS.items():
        if isinstance(exc, error_type):
            status_code = mapped_status
            break
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"code": exc.code, "message": exc.safe_message}},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "riotqueens-api"}


@app.get("/v1/runtime/status")
async def get_runtime_status() -> dict[str, object]:
    base = runtime_status(router)
    return {**base, "conversation_max_turns": conversation_store.max_turns}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> ChatResponse:
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)

    user_id = _actor_user_id(principal, payload.user_id)
    conversation_scope = ConversationScopeKey(
        user_id=user_id,
        character_id=payload.character_id,
        conversation_id=payload.conversation_id,
    )

    async with conversation_store.transaction(conversation_scope):
        await conversation_store.append_user_message(conversation_scope, payload.message)
        try:
            messages = await assemble_request_messages(
                character_id=payload.character_id,
                user_id=user_id,
                conversation_id=payload.conversation_id,
                current_message=payload.message,
                conversation_store=conversation_store,
            )
            request = build_model_request(
                character_id=payload.character_id,
                user_id=user_id,
                conversation_id=payload.conversation_id,
                messages=messages,
            )
            response = await router.generate(request)
            await conversation_store.append_assistant_message(
                conversation_scope, response.content
            )
        except BaseException as error:
            try:
                await conversation_store.pop_last_user_message_if_match(
                    conversation_scope, payload.message
                )
            except BaseException as rollback_error:
                error.add_note(
                    "Failed to roll back the trailing user turn: "
                    f"{type(rollback_error).__name__}"
                )
            raise

    return ChatResponse(response=ChatAssistantResponse(content=response.content))


@app.get("/v1/conversations/{conversation_id}", response_model=ConversationSummary)
async def get_conversation(
    conversation_id: ScopeIdentifier,
    character_id: Annotated[QueenIdentifier, Query()],
    user_id: Annotated[ScopeIdentifier | None, Query()] = None,
    principal: Annotated[Principal | None, Depends(require_principal)] = None,
) -> ConversationSummary:
    _require_registered_queen(character_id)
    _require_current_acceptance(principal)
    actor_user_id = _actor_user_id(principal, user_id)
    scope = ConversationScopeKey(
        user_id=actor_user_id,
        character_id=character_id,
        conversation_id=conversation_id,
    )
    record = await conversation_store.get_conversation(scope)
    if record is None:
        now = datetime.now(UTC)
        return ConversationSummary(
            user_id=actor_user_id,
            character_id=character_id,
            conversation_id=conversation_id,
            messages=[],
            created_at=now,
            updated_at=now,
        )
    return ConversationSummary(
        user_id=record.user_id,
        character_id=record.character_id,
        conversation_id=record.conversation_id,
        messages=[
            ConversationMessageView(
                id=m.id, role=m.role, content=m.content, created_at=m.created_at
            )
            for m in record.messages
        ],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.delete(
    "/v1/conversations/{conversation_id}",
    response_model=ConversationDeleteResponse,
)
async def delete_conversation(
    conversation_id: ScopeIdentifier,
    payload: ConversationScopeRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> ConversationDeleteResponse:
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)
    scope = ConversationScopeKey(
        user_id=_actor_user_id(principal, payload.user_id),
        character_id=payload.character_id,
        conversation_id=conversation_id,
    )
    existed = await conversation_store.delete_conversation(scope)
    return ConversationDeleteResponse(deleted=existed, conversation_id=conversation_id)


@app.get("/v1/consent/status", response_model=ConsentStatusResponse)
async def consent_status(
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> ConsentStatusResponse:
    required = current_acceptance_requirement()
    if not auth_is_required():
        return ConsentStatusResponse(
            accepted=True,
            required_age_gate_version=required.age_gate_version,
            required_terms_version=required.terms_version,
            required_privacy_version=required.privacy_version,
            current=None,
        )
    if principal is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    accepted = snapshot_matches_required(principal.acceptance, required)
    current = None
    if principal.acceptance is not None:
        current = ConsentAcceptRequest(
            age_confirmed=principal.acceptance.age_confirmed,
            age_gate_version=principal.acceptance.age_gate_version,
            terms_version=principal.acceptance.terms_version,
            privacy_version=principal.acceptance.privacy_version,
        )
    return ConsentStatusResponse(
        accepted=accepted,
        required_age_gate_version=required.age_gate_version,
        required_terms_version=required.terms_version,
        required_privacy_version=required.privacy_version,
        current=current,
    )


@app.post("/v1/consent/accept", response_model=ConsentAcceptResponse)
async def consent_accept(
    payload: ConsentAcceptRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
    request: Request,
) -> ConsentAcceptResponse:
    if not auth_is_required():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "auth_required",
                "message": "Clickwrap requires the protected runtime.",
            },
        )
    if principal is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not payload.age_confirmed:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "age_confirmation_required",
                "message": "Age confirmation is required.",
            },
        )
    repo = getattr(request.app.state, "consent_repository", None)
    if repo is None:
        raise HTTPException(status_code=503, detail="Consent store unavailable")
    try:
        record = await repo.record(
            user_id=principal.user_id,
            age_confirmed=payload.age_confirmed,
            age_gate_version=payload.age_gate_version,
            terms_version=payload.terms_version,
            privacy_version=payload.privacy_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_acceptance", "message": str(exc)},
        ) from exc
    # Refresh principal acceptance for subsequent requests in-process identity cache
    # is re-resolved from DB on next token; ok.
    return ConsentAcceptResponse(
        acceptance_id=record.acceptance_id,
        accepted_at=record.accepted_at,
        age_gate_version=record.age_gate_version,
        terms_version=record.terms_version,
        privacy_version=record.privacy_version,
        document_digest=record.document_digest,
    )
