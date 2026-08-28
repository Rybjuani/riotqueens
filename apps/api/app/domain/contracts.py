"""Thin public/internal contracts for the nuclear API (no memories, no cape)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

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


class MessageInput(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    # System may carry the full DOSSIER_MAESTRO.md (Owner: load complete dossier).
    content: str = Field(min_length=1, max_length=200_000)


class ModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route: Route
    character_id: str
    user_id: str
    conversation_id: str
    messages: list[MessageInput] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ModelResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Usage = Field(default_factory=Usage)
    latency_ms: int = 0
    retry_count: int = 0
    finish_reason: str | None = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier
    conversation_id: ScopeIdentifier
    message: str = Field(min_length=1, max_length=4_000)


class ChatAssistantResponse(BaseModel):
    content: str


class ChatResponse(BaseModel):
    response: ChatAssistantResponse


class RootSystemMode(StrEnum):
    BARDERA = "bardera"
    EMPTY = "empty"
    CUSTOM = "custom"


class OwnerConsoleChatRequest(BaseModel):
    """Shared body for /v1/usuario/chat, /v1/root/chat, /v1/compare."""

    model_config = ConfigDict(extra="forbid")
    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier
    conversation_id: ScopeIdentifier
    message: str = Field(min_length=1, max_length=4_000)
    system: RootSystemMode = RootSystemMode.EMPTY
    custom_system: str | None = Field(default=None, min_length=1, max_length=200_000)
    persist: bool = False
    max_tokens: int | None = Field(default=None, ge=1, le=8_192)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    frequency_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    model: str | None = Field(default=None, min_length=1, max_length=256)

    @model_validator(mode="after")
    def _custom_system_required(self) -> "OwnerConsoleChatRequest":
        if self.system == RootSystemMode.CUSTOM and not self.custom_system:
            raise ValueError("custom_system is required when system=custom")
        if self.system != RootSystemMode.CUSTOM and self.custom_system:
            raise ValueError("custom_system is only allowed when system=custom")
        return self


class OwnerChatResponse(BaseModel):
    response: ChatAssistantResponse
    owner: dict[str, Any]


class CompareSideResult(BaseModel):
    content: str | None = None
    owner: dict[str, Any] | None = None


class CompareResponse(BaseModel):
    usuario: CompareSideResult
    root: CompareSideResult
    diff: dict[str, Any]
    errors: dict[str, Any | None] = Field(
        default_factory=lambda: {"usuario": None, "root": None}
    )


class ConversationMessageView(BaseModel):
    id: str
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    user_id: str
    character_id: str
    conversation_id: str
    messages: list[ConversationMessageView] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationScopeRequest(BaseModel):
    user_id: ScopeIdentifier | None = None
    character_id: QueenIdentifier


class ConversationDeleteResponse(BaseModel):
    deleted: bool
    conversation_id: str


class ConsentAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_confirmed: bool
    age_gate_version: str = Field(min_length=1, max_length=32)
    terms_version: str = Field(min_length=1, max_length=32)
    privacy_version: str = Field(min_length=1, max_length=32)


class ConsentStatusResponse(BaseModel):
    accepted: bool
    required_age_gate_version: str
    required_terms_version: str
    required_privacy_version: str
    current: ConsentAcceptRequest | None = None


class ConsentAcceptResponse(BaseModel):
    acceptance_id: str
    accepted_at: datetime
    age_gate_version: str
    terms_version: str
    privacy_version: str
    document_digest: str
