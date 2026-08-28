import os
from contextlib import asynccontextmanager
from datetime import UTC
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
    MemoryCreateRequest,
    MemoryDeleteResponse,
    MemoryListResponse,
    MemoryRecordView,
    QueenIdentifier,
    Route,
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
from .domain.memories import (
    InProcessMemoryStore,
    MemoryScopeKey,
    PostgresMemoryStore,
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
    """Read an int env var, falling back to default on missing/invalid."""
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


# Default in-process stores. When DATABASE_URL is set, lifespan swaps them
# for Postgres-backed implementations without changing handlers.
_CONVERSATION_MAX_TURNS = _env_int_optional("RIOTQUEENS_CONVERSATION_MAX_TURNS", 8)
_MEMORY_MAX_PER_SCOPE = _env_int_optional("RIOTQUEENS_MEMORY_MAX_PER_SCOPE", 32)

conversation_store: InProcessConversationStore | PostgresConversationStore = (
    InProcessConversationStore(max_turns=_CONVERSATION_MAX_TURNS)
)
memory_store: InProcessMemoryStore | PostgresMemoryStore = InProcessMemoryStore(
    max_per_scope=_MEMORY_MAX_PER_SCOPE
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open Postgres pool for identity, consent, conversations and memories."""

    global conversation_store, memory_store
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        import asyncpg

        # SQLAlchemy-style URLs are accepted in the shared env contract.
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
        memory_store = PostgresMemoryStore(pool, max_per_scope=_MEMORY_MAX_PER_SCOPE)
    yield
    pool = getattr(app.state, "db_pool", None) or getattr(app.state, "identity_pool", None)
    if pool is not None:
        await pool.close()


app = FastAPI(title="RiotQueens API", version="0.5.0", lifespan=lifespan)


class NoStoreV1Middleware:
    """Prevent browsers and intermediaries from caching stateful API responses."""

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
    """Reject unknown Queens before allocating scope state or calling a provider."""

    if not is_registered_queen(character_id):
        raise HTTPException(
            status_code=404,
            detail={
                "code": "queen_not_found",
                "message": "Queen is not available.",
            },
        )


def _actor_user_id(principal: Principal | None, browser_user_id: str | None) -> str:
    """Return a token-derived actor identity; legacy test mode is explicit."""

    if auth_is_required():
        if principal is None:  # Defensive: dependency must already have failed closed.
            raise HTTPException(status_code=401, detail="Unauthorized")
        return principal.user_id
    if browser_user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return browser_user_id


def _require_current_acceptance(principal: Principal | None) -> None:
    """Fail closed on protected product surfaces without a current clickwrap."""

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
    """Map sanitized provider failures to stable 5xx responses.

    Upstream auth failures are intentionally NOT exposed as user-facing 401/403.
    The response contains only a stable code and controlled safe message.
    """
    status_code = 503
    for error_type, mapped_status in _PROVIDER_HTTP_STATUS.items():
        if isinstance(exc, error_type):
            status_code = mapped_status
            break
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": {
                "code": exc.code,
                "message": exc.safe_message,
            }
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "riotqueens-api"}


@app.get("/v1/runtime/status")
async def get_runtime_status() -> dict[str, object]:
    """Safe provider diagnostics, plus prototype state-store config.

    The returned fields never include API keys, Authorization headers,
    URLs with sensitive query, or internal stacks. The
    ``conversation_max_turns`` and ``memory_max_per_scope`` fields are
    safe config values; the actual stored messages and memory contents
    are never surfaced here.
    """
    base = runtime_status(router)
    return {
        **base,
        "conversation_max_turns": conversation_store.max_turns,
        "memory_max_per_scope": memory_store.max_per_scope,
    }


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> ChatResponse:
    """Send a single chat message and rebuild canonical server context.

    The frontend sends ONLY the current user message plus the scope
    identifiers (`user_id`, `character_id`, `conversation_id`). The
    server, holding the per-scope transaction lock for the WHOLE turn
    lifecycle:

      1. Acquires the per-conversation transaction lock (reentrant).
         Two concurrent requests to the SAME conversation serialize
         completely — their append/context/provider/append mutations
         cannot interleave. Different conversations run in parallel.
      2. Appends the user message to the in-process conversation store
         (scoped by user + character + conversation).
      3. Assembles the canonical messages list:
         system Queen prompt → server-owned memory context → bounded
         conversation history (which now ends with the trailing user
         message) → defensive current-user append if needed.
      4. Calls the provider via the ModelRouter. Any exception or task
         cancellation after the user append attempts to roll that exact
         trailing message back, so no failed half-turn pollutes history.
         The original error is always re-raised; typed provider failures
         still reach FastAPI's sanitized exception handler.
      5. On success, appends the assistant's validated content as a new
         assistant turn. The stored record is then pruned to the bound
         so in-process state does not grow without limit. (If the
         router's `OutputValidator` ultimately substituted
         `SAFE_FALLBACK_CONTENT`, that fallback IS the assistant
         response the user sees — so it is stored as a real assistant
         turn, per Issue #5.)

    The client never sends a system prompt, never sends trusted prior
    messages, never sends trusted memories. The browser only sends the
    current message and the scope identifiers. Model routing is also
    server-owned: this public endpoint always uses ``FAST_CHAT``.
    """
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)

    user_id = _actor_user_id(principal, payload.user_id)
    conversation_scope = ConversationScopeKey(
        user_id=user_id,
        character_id=payload.character_id,
        conversation_id=payload.conversation_id,
    )

    # Acquire the per-scope transaction lock for the WHOLE turn. This
    # serializes same-conversation requests end-to-end (append user →
    # provider call → append assistant / rollback). Different
    # conversations use different locks and run in parallel. A slow
    # provider in one conversation does NOT block other conversations.
    async with conversation_store.transaction(conversation_scope):
        # 1. Append the user message BEFORE calling the provider. This
        #    becomes the trailing user turn in the bounded history.
        await conversation_store.append_user_message(conversation_scope, payload.message)

        try:
            # 2. Assemble the canonical messages list and build the
            #    provider-independent internal request.
            messages = await assemble_request_messages(
                character_id=payload.character_id,
                user_id=user_id,
                conversation_id=payload.conversation_id,
                current_message=payload.message,
                route=Route.FAST_CHAT,
                conversation_store=conversation_store,
                memory_store=memory_store,
            )

            request = build_model_request(
                route=Route.FAST_CHAT,
                character_id=payload.character_id,
                user_id=user_id,
                conversation_id=payload.conversation_id,
                messages=messages,
            )

            # 3. Call the provider, then store exactly the validated
            #    content returned to the public response.
            response = await router.generate(request)
            await conversation_store.append_assistant_message(
                conversation_scope, response.content
            )
        except BaseException as error:
            # Cancellation inherits from BaseException, not Exception.
            # Rollback runs while this task still owns the reentrant turn
            # lock. Preserve the original failure even if the best-effort
            # rollback itself unexpectedly fails.
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


# ---------------------------------------------------------------------- #
# Conversation inspect / delete APIs (Issue #5 task 8)
# ---------------------------------------------------------------------- #


@app.get(
    "/v1/conversations/{conversation_id}",
    response_model=ConversationSummary,
)
async def get_conversation(
    conversation_id: ScopeIdentifier,
    character_id: Annotated[QueenIdentifier, Query()],
    user_id: Annotated[ScopeIdentifier | None, Query()] = None,
    principal: Annotated[Principal | None, Depends(require_principal)] = None,
) -> ConversationSummary:
    """Return the stored messages for one conversation scope.

    Scope is enforced by `(user_id, character_id, conversation_id)`. A
    different user / character / conversation id CANNOT see this
    conversation's messages. Returns an empty message list (with the
    scope identifiers echoed back) if the conversation does not exist
    yet — this is graceful for a fresh browser session.

    """
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
        # Return an empty summary with the scope echoed back. Use a
        # stable created_at/updated_at = now so the response shape is
        # consistent.
        from datetime import datetime

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
    """Clear the in-process conversation state for one scope.

    Only the conversation matching the body's `user_id` +
    `character_id` + the path's `conversation_id` is deleted. Other
    conversations — same user different conversation, different user,
    different character — are NOT touched.

    Returns ``{"deleted": bool, "conversation_id": str}`` where
    ``deleted`` is True iff a conversation existed and was removed.
    """
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)

    scope = ConversationScopeKey(
        user_id=_actor_user_id(principal, payload.user_id),
        character_id=payload.character_id,
        conversation_id=conversation_id,
    )
    existed = await conversation_store.delete_conversation(scope)
    return ConversationDeleteResponse(deleted=existed, conversation_id=conversation_id)


# ---------------------------------------------------------------------- #
# Memory APIs (Issue #5 task 7)
# ---------------------------------------------------------------------- #


@app.get("/v1/memories", response_model=MemoryListResponse)
async def list_memories(
    character_id: Annotated[QueenIdentifier, Query()],
    user_id: Annotated[ScopeIdentifier | None, Query()] = None,
    principal: Annotated[Principal | None, Depends(require_principal)] = None,
) -> MemoryListResponse:
    """List the explicit user-fact memories for one scope.

    Scope is enforced by `(user_id, character_id)`. A different user or
    character CANNOT see this scope's memories. Returns an empty list
    if no memories exist yet.

    """
    _require_registered_queen(character_id)
    _require_current_acceptance(principal)

    actor_user_id = _actor_user_id(principal, user_id)
    scope = MemoryScopeKey(user_id=actor_user_id, character_id=character_id)
    records = await memory_store.list_memories(scope)
    return MemoryListResponse(
        memories=[
            MemoryRecordView(
                id=r.id,
                user_id=r.user_id,
                character_id=r.character_id,
                content=r.content,
                memory_type=r.memory_type,
                source=r.source,
                confidence=r.confidence,
                inferred=r.inferred,
                created_at=r.created_at,
            )
            for r in records
        ],
        count=len(records),
    )


@app.post("/v1/memories", response_model=MemoryRecordView, status_code=201)
async def create_memory(
    payload: MemoryCreateRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> MemoryRecordView:
    """Add an explicit user-fact memory.

    The client supplies only `content` (1-500 chars) and the scope
    identifiers. The server sets `memory_type=user_fact`,
    `source=explicit_user_statement`, `confidence=high`, `inferred=False`.
    The client CANNOT use this endpoint to upload a system prompt,
    trusted role messages, or arbitrary provider instructions —
    `content` is stored verbatim as a fact and injected as a separate
    server-owned memory section in the model request.

    If the scope exceeds `RIOTQUEENS_MEMORY_MAX_PER_SCOPE`, the oldest
    memory is evicted (FIFO).
    """
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)

    scope = MemoryScopeKey(
        user_id=_actor_user_id(principal, payload.user_id),
        character_id=payload.character_id,
    )
    record = await memory_store.add_memory(scope, payload.content)
    return MemoryRecordView(
        id=record.id,
        user_id=record.user_id,
        character_id=record.character_id,
        content=record.content,
        memory_type=record.memory_type,
        source=record.source,
        confidence=record.confidence,
        inferred=record.inferred,
        created_at=record.created_at,
    )


@app.delete("/v1/memories/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: ScopeIdentifier,
    payload: ConversationScopeRequest,
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> MemoryDeleteResponse:
    """Delete a single explicit user-fact memory by id within a scope.

    The scope check is MANDATORY: a memory id from a different user or
    character CANNOT be deleted through this endpoint. Returns 404
    (via `deleted=False`) if the memory id is unknown within the scope.

    """
    _require_registered_queen(payload.character_id)
    _require_current_acceptance(principal)

    scope = MemoryScopeKey(
        user_id=_actor_user_id(principal, payload.user_id),
        character_id=payload.character_id,
    )
    deleted = await memory_store.delete_memory(scope, memory_id)
    if not deleted:
        # Clean 404 for unknown id within scope. We do NOT leak whether
        # the id exists in a different scope — that would be an
        # information-disclosure side channel.
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "memory_not_found",
                    "message": "Memory not found within the requested scope.",
                }
            },
        )
    return MemoryDeleteResponse(deleted=True, memory_id=memory_id)


# ---------------------------------------------------------------------- #
# Clickwrap consent (ADR 0004)
# ---------------------------------------------------------------------- #


@app.get("/v1/consent/status", response_model=ConsentStatusResponse)
async def consent_status(
    principal: Annotated[Principal | None, Depends(require_principal)],
) -> ConsentStatusResponse:
    """Return whether the actor holds a current clickwrap package."""

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
    """Record an append-only clickwrap acceptance for the authenticated actor."""

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
        raise HTTPException(
            status_code=503,
            detail={
                "code": "consent_unavailable",
                "message": "Consent store is unavailable.",
            },
        )
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
            detail={
                "code": "invalid_acceptance",
                "message": str(exc),
            },
        ) from exc
    # Refresh in-process principal is request-scoped; next request reloads
    # acceptance from Postgres via the identity repository.
    return ConsentAcceptResponse(
        acceptance_id=record.acceptance_id,
        accepted_at=record.accepted_at,
        age_gate_version=record.age_gate_version,
        terms_version=record.terms_version,
        privacy_version=record.privacy_version,
        document_digest=record.document_digest,
    )
