"""Server-side context assembly for multi-turn conversation + memory.

This module is the single place that decides what `messages` list the
provider receives. It composes the request in this STRICT order:

    1. Canonical Queen system prompt (`queens.get_system_prompt`)
       — server-owned, re-prepended on EVERY request, NEVER stored.
    2. Server-owned memory context (`memories.memory_context_section`)
       — built from scoped explicit user facts, as a SEPARATE system
       block, never mixed into the Queen prompt.
    3. Server-owned voice exemplars (`queens.get_voice_exemplars`)
       — few-shot style anchors for the Queen; never stored as history.
    4. Bounded conversation history (`conversations.get_history`)
       — prior user + assistant turns, scoped by
       (user_id, character_id, conversation_id). Bound by
       `RIOTQUEENS_CONVERSATION_MAX_TURNS` (complete pairs only).
    5. Current user message (`ChatRequest.message`).

The frontend NEVER sends a system prompt, never sends trusted prior
messages, never sends trusted memories. The browser only sends the
current message and the scope identifiers. The server rebuilds the
full canonical context from its own state.

State integrity
---------------
The chat handler owns the complete turn transaction for one conversation:

1. acquire the per-conversation reentrant lock;
2. append the current user message;
3. assemble server-owned context and call the provider while still holding
   that conversation lock;
4. append the validated assistant turn on success, or remove the just-added
   user message on any later exception or task cancellation;
5. release the lock.

Holding the lock across the provider call deliberately serializes turns for
the same conversation, while independent conversation scopes continue in
parallel. A failed request therefore leaves no half-turn behind and a retry
starts from the last confirmed history. See `main.py` for orchestration and
`conversations.py` for the transaction and rollback contracts.
"""

from __future__ import annotations

from .contracts import MessageInput, ModelRequest, Route
from .conversations import (
    ConversationScopeKey,
    ConversationStore,
    stored_to_message_input,
)
from .memories import MemoryScopeKey, MemoryStore, memory_context_section
from .queens import get_system_prompt, get_voice_exemplars


async def assemble_request_messages(
    *,
    character_id: str,
    user_id: str,
    conversation_id: str,
    current_message: str,
    route: Route,
    conversation_store: ConversationStore,
    memory_store: MemoryStore,
) -> list[MessageInput]:
    """Build the canonical `messages` list for a model request.

    Order is fixed:
      1. Canonical Queen system prompt (server-owned, never stored).
      2. Server-owned memory context (separate system block, only if
         the user has explicit memories).
      3. Server-owned voice exemplars (few-shot style; never stored).
      4. Bounded conversation history (prior user/assistant turns).
      5. Current user message.

    The current user message is appended to the conversation store
    BEFORE this function is called (by the chat handler), so the
    bounded history returned by `conversation_store.get_history` will
    include it as the trailing user turn. This function does NOT append
    it again — it relies on the history snapshot.
    """
    messages: list[MessageInput] = []

    # 1. Canonical Queen system prompt.
    system_prompt = get_system_prompt(character_id)
    if system_prompt:
        messages.append(MessageInput(role="system", content=system_prompt))

    # 2. Server-owned memory context (separate system block).
    memory_scope = MemoryScopeKey(user_id=user_id, character_id=character_id)
    memories = await memory_store.list_memories(memory_scope)
    memory_section = memory_context_section(memories)
    if memory_section is not None:
        messages.append(MessageInput(role="system", content=memory_section))

    # 3. Server-owned voice exemplars (style anchors; not conversation state).
    # Bracket them so the model does not treat few-shot turns as live history
    # (e.g. "ya me preguntaste eso" when the user reuses a similar opener).
    exemplars = get_voice_exemplars(character_id)
    if exemplars:
        messages.append(
            MessageInput(
                role="system",
                content=(
                    "Anclas de estilo de la Queen (ejemplos de voz). "
                    "NO son mensajes de este usuario, NO son recuerdos del "
                    "chat actual y NO cuentan como turns previos. Imitá el "
                    "criterio y la densidad cuando el tema lo pida; no "
                    "asumas que ya ocurrieron."
                ),
            )
        )
        messages.extend(exemplars)
        messages.append(
            MessageInput(
                role="system",
                content=(
                    "Fin de anclas de estilo. A partir de acá es el chat real "
                    "con este usuario. Respondé solo al último mensaje user "
                    "del chat real, con la voz de la Queen."
                ),
            )
        )

    # 4. Bounded conversation history (includes the trailing current
    #    user message that was just appended by the chat handler).
    conversation_scope = ConversationScopeKey(
        user_id=user_id,
        character_id=character_id,
        conversation_id=conversation_id,
    )
    history = await conversation_store.get_history(conversation_scope)
    for stored in history:
        messages.append(stored_to_message_input(stored))

    # Defensive: if the current user message was somehow not in the
    # bounded history (e.g. max_turns=0 and the trailing-user
    # preservation was bypassed), append it explicitly so the request
    # always carries the user's current message.
    if not _ends_with_user_message(messages, current_message):
        messages.append(MessageInput(role="user", content=current_message))

    return messages


def _ends_with_user_message(messages: list[MessageInput], content: str) -> bool:
    """Return True if the last message is a user message with this content."""
    if not messages:
        return False
    last = messages[-1]
    return last.role == "user" and last.content == content


def build_model_request(
    *,
    route: Route,
    character_id: str,
    user_id: str,
    conversation_id: str,
    messages: list[MessageInput],
) -> ModelRequest:
    """Construct a `ModelRequest` from the assembled messages.

    The `memories` field on `ModelRequest` is left empty in this
    milestone — memories are injected as a dedicated system message
    block, NOT through the legacy `memories` list field. This keeps
    the memory context visible to the OpenAI-compatible provider's
    chat-completions API (which only understands `messages`).
    """
    return ModelRequest(
        route=route,
        character_id=character_id,
        user_id=user_id,
        conversation_id=conversation_id,
        messages=messages,
    )


__all__ = [
    "assemble_request_messages",
    "build_model_request",
]
