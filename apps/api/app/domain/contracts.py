"""Thin public/internal contracts for the nuclear API (no memories, no cape)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

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
    content: str = Field(min_length=1, max_length=20_000)


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
