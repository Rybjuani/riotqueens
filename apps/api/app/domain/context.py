"""Assemble provider messages: preset + conversation history only. No memories. No cape."""

from __future__ import annotations

from .contracts import MessageInput, ModelRequest, Route
from .conversations import ConversationScopeKey, ConversationStore, stored_to_message_input
from .queens import get_system_prompt


async def assemble_request_messages(
    *,
    character_id: str,
    user_id: str,
    conversation_id: str,
    current_message: str,
    conversation_store: ConversationStore,
) -> list[MessageInput]:
    messages: list[MessageInput] = []
    system_prompt = get_system_prompt(character_id)
    if system_prompt:
        messages.append(MessageInput(role="system", content=system_prompt))

    conversation_scope = ConversationScopeKey(
        user_id=user_id,
        character_id=character_id,
        conversation_id=conversation_id,
    )
    history = await conversation_store.get_history(conversation_scope)
    for stored in history:
        messages.append(stored_to_message_input(stored))

    if not messages or messages[-1].role != "user" or messages[-1].content != current_message:
        messages.append(MessageInput(role="user", content=current_message))
    return messages


def build_model_request(
    *,
    character_id: str,
    user_id: str,
    conversation_id: str,
    messages: list[MessageInput],
) -> ModelRequest:
    return ModelRequest(
        route=Route.FAST_CHAT,
        character_id=character_id,
        user_id=user_id,
        conversation_id=conversation_id,
        messages=messages,
    )
