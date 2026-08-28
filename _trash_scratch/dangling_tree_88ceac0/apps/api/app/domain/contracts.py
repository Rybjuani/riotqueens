from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Public scope identifiers are opaque tokens, not free-form text. Bounding
# them at the API contract prevents oversized, whitespace-variant keys from
# reaching in-process store dictionaries and their per-scope lock maps.
ScopeIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    ),
]
QueenIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9-]{0,63}$",
    ),
]


class Route(StrEnum):
    FAST_CHAT = "fast_chat"
    CREATIVE_CHAT = "creative_chat"
    DEEP_REASONING = "deep_reasoning"
    VISION = "vision"
    AGENT_TASK = "agent_task"
    MEMORY = "memory"


class MediaType(StrEnum):
    """Media kinds reserved for a future authorized delivery path."""

    SELFIE = "selfie"
    IMAGE = "image"


class MediaIntent(BaseModel):
    """Server-owned request to resolve an authorized media asset.

    This is an internal domain contract, not a public endpoint. It carries
    semantic intent only; entitlement, consent, asset selection, object keys,
    URLs and delivery permissions remain backend-owned and are deliberately
    absent from the model.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: ScopeIdentifier
    character_id: QueenIdentifier
    conversation_id: ScopeIdentifier
    media_type: MediaType
    mood: str | None = Field(default=None, max_length=64)
    context: str | None = Field(default=None, max_length=500)


class MessageInput(BaseModel):
    role: str = Field(pattern="^(system|user|assistant|tool)$")
    content: str = Field(min_length=1, max_length=20_000)


class ModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route: Route
    character_id: str
    user_id: str
    conversation_id: str
    messages: list[MessageInput] = Field(min_length=1)
    memories: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class OutputValidationResult(BaseModel):
    is_valid: bool
    language_ok: bool
    encoding_ok: bool
    not_truncated: bool
    not_repetitive: bool
    no_internal_leak: bool
    character_consistent: bool
    reasons: list[str] = Field(default_factory=list)


class ModelResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Usage = Field(default_factory=Usage)
    latency_ms: int = 0
    validation: OutputValidationResult | None = None
    retry_count: int = 0


class ChatRequest(BaseModel):
    """Public chat input; model routing remains a server responsibility."""

    model_config = ConfigDict(extra="forbid")

    # Deprecated compatibility field. It is ignored whenever authentication is
    # enabled; the server derives the actor from the verified token.
    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier
    conversation_id: ScopeIdentifier
    message: str = Field(min_length=1, max_length=4_000)


class ChatAssistantResponse(BaseModel):
    """Stable public subset of an internal model response."""

    content: str


class ChatResponse(BaseModel):
    response: ChatAssistantResponse


# ---------------------------------------------------------------------- #
# Conversation & memory API contracts (Issue #5)
# ---------------------------------------------------------------------- #
#
# These contracts back the /v1/conversations and /v1/memories endpoints.
# They are intentionally small and explicit. There is NO auth in this
# milestone — `user_id` and `character_id` are prototype scope keys,
# not secure identities. The handoff doc records this limitation
# honestly.


class ConversationMessageView(BaseModel):
    """API view of a single stored conversation message.

    Only ``user`` and ``assistant`` roles are ever stored; the canonical
    Queen system prompt is NEVER persisted and is never returned here.
    """

    id: str
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """API view of a full conversation, scoped by (user, character, conversation).

    Returned by `GET /v1/conversations/{conversation_id}`. The
    `messages` list is ordered oldest-first. System prompts are never
    included.
    """

    user_id: str
    character_id: str
    conversation_id: str
    messages: list[ConversationMessageView] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationScopeRequest(BaseModel):
    """Explicit scope body for conversation and memory deletion."""

    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier


class MemoryCreateRequest(BaseModel):
    """Body for `POST /v1/memories` — add an explicit user fact.

    The client supplies only ``content`` plus the scope identifiers.
    The server sets ``memory_type``, ``source``, ``confidence`` and
    ``inferred`` — never the client.

    The client CANNOT use this endpoint to upload a system prompt,
    trusted role messages, or arbitrary provider instructions. The
    only field that affects model context is ``content``, which is
    stored verbatim as a fact and injected as a separate system-owned
    memory section.
    """

    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier
    content: str = Field(min_length=1, max_length=500)


class MemoryRecordView(BaseModel):
    """API view of a single stored memory record."""

    id: str
    user_id: str
    character_id: str
    content: str
    memory_type: str
    source: str
    confidence: str
    inferred: bool
    created_at: datetime


class MemoryListResponse(BaseModel):
    """Response for `GET /v1/memories`."""

    memories: list[MemoryRecordView]
    count: int


class MemoryDeleteResponse(BaseModel):
    """Response for `DELETE /v1/memories/{memory_id}`."""

    deleted: bool
    memory_id: str


class ConversationDeleteResponse(BaseModel):
    """Response for `DELETE /v1/conversations/{conversation_id}`."""

    deleted: bool
    conversation_id: str


# ---------------------------------------------------------------------- #
# Clickwrap consent (ADR 0004)
# ---------------------------------------------------------------------- #


class ConsentAcceptRequest(BaseModel):
    """Client-presented clickwrap confirmations and versions shown."""

    model_config = ConfigDict(extra="forbid")

    age_confirmed: bool
    age_gate_version: str = Field(min_length=1, max_length=32)
    terms_version: str = Field(min_length=1, max_length=32)
    privacy_version: str = Field(min_length=1, max_length=32)


class ConsentStatusResponse(BaseModel):
    """Whether the actor holds a current acceptance for protected access."""

    accepted: bool
    required_age_gate_version: str
    required_terms_version: str
    required_privacy_version: str
    current: ConsentAcceptRequest | None = None


class ConsentAcceptResponse(BaseModel):
    """Server-stamped acceptance event."""

    acceptance_id: str
    accepted_at: datetime
    age_gate_version: str
    terms_version: str
    privacy_version: str
    document_digest: str
