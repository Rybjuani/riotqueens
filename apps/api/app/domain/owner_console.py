"""Owner Console pipelines: usuario (prod+trace), root (raw), compare."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from .context import assemble_request_messages, build_model_request
from .contracts import (
    MessageInput,
    ModelRequest,
    ModelResponse,
    OwnerConsoleChatRequest,
    RootSystemMode,
    Route,
)
from .conversations import (
    ConversationScopeKey,
    ConversationStore,
    stored_to_message_input,
)
from .owner import (
    FallbackTrace,
    LocalGuardTrace,
    MemoryTrace,
    OwnerTrace,
    RewriteTrace,
    RollbackTrace,
)
from .providers.errors import (
    ProviderContentBlockedError,
    ProviderError,
    ProviderUpstreamError,
)
from .providers.openai_compatible import OpenAICompatibleProvider
from .queens import get_system_prompt
from .router import ModelRouter


@dataclass
class TurnSuccess:
    content: str
    trace: OwnerTrace


@dataclass
class TurnFailure:
    trace: OwnerTrace
    error: ProviderError
    detail: dict[str, Any]


def _pair_count(history_len: int) -> int:
    return history_len // 2


def _memory_trace(*, history_messages: int, max_turns: int) -> MemoryTrace:
    at_cap = max_turns > 0 and _pair_count(history_messages) >= max_turns
    if at_cap:
        return MemoryTrace(
            lost=True,
            detail=f"context window at max_turns={max_turns}; older pairs retained in durable store",
        )
    return MemoryTrace(lost=False, detail=None)


def _primary_provider(router: ModelRouter):
    return router.providers[Route.FAST_CHAT]


def _fallback_info(router: ModelRouter) -> FallbackTrace:
    fallbacks = router.fallback_providers.get(Route.FAST_CHAT, ())
    if not fallbacks:
        return FallbackTrace(configured=False, used=False, model=None)
    return FallbackTrace(configured=True, used=False, model=fallbacks[0].model)


def _provider_sampling(provider: Any) -> tuple[int | None, float | None]:
    max_tokens = getattr(provider, "max_tokens", None)
    temperature = getattr(provider, "temperature", None)
    return (
        int(max_tokens) if isinstance(max_tokens, int) else None,
        float(temperature) if isinstance(temperature, (int, float)) else None,
    )


async def _snapshot_history(
    store: ConversationStore, scope: ConversationScopeKey
) -> list[MessageInput]:
    history = await store.get_history(scope)
    return [stored_to_message_input(msg) for msg in history]


def _build_root_messages(
    *,
    system_mode: RootSystemMode,
    custom_system: str | None,
    character_id: str,
    history: list[MessageInput],
    current_message: str,
) -> tuple[list[MessageInput], str]:
    messages: list[MessageInput] = []
    system_label = system_mode.value
    if system_mode == RootSystemMode.BARDERA:
        prompt = get_system_prompt(character_id)
        if prompt:
            messages.append(MessageInput(role="system", content=prompt))
    elif system_mode == RootSystemMode.CUSTOM:
        assert custom_system is not None
        messages.append(MessageInput(role="system", content=custom_system))
    # empty: no system message at all — no diagnostic injection

    messages.extend(history)
    if not messages or messages[-1].role != "user" or messages[-1].content != current_message:
        messages.append(MessageInput(role="user", content=current_message))
    return messages, system_label


def _failure_detail(error: ProviderError, *, channel: str, trace: OwnerTrace) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "code": error.code,
        "message": error.safe_message,
        "owner": trace.to_dict(),
    }
    if isinstance(error, ProviderUpstreamError) and error.upstream is not None:
        detail["upstream"] = error.upstream
    elif error.upstream is not None and channel == "root":
        detail["upstream"] = error.upstream
    return detail


async def run_usuario_turn(
    *,
    router: ModelRouter,
    conversation_store: ConversationStore,
    user_id: str,
    payload: OwnerConsoleChatRequest,
    persist: bool = True,
    history_snapshot: list[MessageInput] | None = None,
) -> TurnSuccess:
    """Production-identical pipeline with Owner telemetry. Raises TurnFailure via exception path.

    On provider failure raises the original ProviderError after attaching ``.owner_failure``.
    """
    scope = ConversationScopeKey(
        user_id=user_id,
        character_id=payload.character_id,
        conversation_id=payload.conversation_id,
    )
    max_turns = int(getattr(conversation_store, "max_turns", 8))
    primary = _primary_provider(router)
    primary_max_tokens, primary_temperature = _provider_sampling(primary)
    fallback_trace = _fallback_info(router)
    primary_model = getattr(primary, "model", None)

    rollback = RollbackTrace()
    started = perf_counter()

    async def _execute() -> TurnSuccess:
        nonlocal rollback
        if persist:
            await conversation_store.append_user_message(scope, payload.message)
            messages = await assemble_request_messages(
                character_id=payload.character_id,
                user_id=user_id,
                conversation_id=payload.conversation_id,
                current_message=payload.message,
                conversation_store=conversation_store,
            )
        else:
            if history_snapshot is not None:
                history = list(history_snapshot)
            else:
                history = await _snapshot_history(conversation_store, scope)
            messages = []
            prompt = get_system_prompt(payload.character_id)
            if prompt:
                messages.append(MessageInput(role="system", content=prompt))
            messages.extend(history)
            messages.append(MessageInput(role="user", content=payload.message))

        history_messages = len([m for m in messages if m.role != "system"])
        memory = _memory_trace(history_messages=history_messages, max_turns=max_turns)
        request = build_model_request(
            character_id=payload.character_id,
            user_id=user_id,
            conversation_id=payload.conversation_id,
            messages=messages,
        )

        try:
            response = await router.generate(request)
        except ProviderError as error:
            if persist:
                rollback.attempted = True
                try:
                    ok = await conversation_store.pop_last_user_message_if_match(
                        scope, payload.message
                    )
                    rollback.succeeded = bool(ok)
                    if not ok:
                        memory = MemoryTrace(
                            lost=True,
                            detail="rollback did not remove trailing user turn",
                        )
                    else:
                        memory = MemoryTrace(
                            lost=False,
                            detail="trailing user turn rolled back",
                        )
                except Exception as rollback_error:  # noqa: BLE001 — must surface honestly
                    rollback.succeeded = False
                    memory = MemoryTrace(
                        lost=True,
                        detail=f"rollback failed: {type(rollback_error).__name__}",
                    )
            guard = LocalGuardTrace(
                triggered=isinstance(error, ProviderContentBlockedError),
                reason=error.code if isinstance(error, ProviderContentBlockedError) else None,
            )
            trace = OwnerTrace(
                channel="usuario",
                system="bardera",
                history_messages=history_messages,
                max_turns=max_turns,
                truncated=memory.lost and "max_turns" in (memory.detail or ""),
                max_tokens=primary_max_tokens,
                temperature=primary_temperature,
                provider=getattr(primary, "name", None),
                model=str(primary_model) if primary_model else None,
                local_guard=guard,
                fallback=fallback_trace,
                rewrite=RewriteTrace(applied=True, ops=["strip_controls", "anti_leak"]),
                latency_ms=round((perf_counter() - started) * 1000),
                rollback=rollback,
                memory=memory,
                blocked=isinstance(error, ProviderContentBlockedError),
            )
            failure = TurnFailure(
                trace=trace,
                error=error,
                detail=_failure_detail(error, channel="usuario", trace=trace),
            )
            error.owner_failure = failure  # type: ignore[attr-defined]
            raise

        if persist:
            await conversation_store.append_assistant_message(scope, response.content)

        used_fallback = bool(
            fallback_trace.configured
            and response.model
            and primary_model
            and response.model != primary_model
        )
        fallback_trace.used = used_fallback

        rewrite_ops = ["strip_controls"]
        # anti-leak only mutates control when it rejects; success means it ran and passed
        rewrite_ops.append("anti_leak_check")

        trace = OwnerTrace(
            channel="usuario",
            system="bardera",
            history_messages=history_messages,
            max_turns=max_turns,
            truncated=memory.lost,
            max_tokens=primary_max_tokens,
            temperature=primary_temperature,
            provider=response.provider,
            model=response.model,
            local_guard=LocalGuardTrace(triggered=False),
            fallback=fallback_trace,
            rewrite=RewriteTrace(applied=True, ops=rewrite_ops),
            latency_ms=response.latency_ms or round((perf_counter() - started) * 1000),
            retry_count=response.retry_count,
            rollback=rollback,
            memory=memory,
            finish_reason=response.finish_reason,
        )
        return TurnSuccess(content=response.content, trace=trace)

    if persist:
        async with conversation_store.transaction(scope):
            return await _execute()
    return await _execute()


async def run_root_turn(
    *,
    router: ModelRouter,
    conversation_store: ConversationStore,
    user_id: str,
    payload: OwnerConsoleChatRequest,
    history_snapshot: list[MessageInput] | None = None,
) -> TurnSuccess:
    """Raw Euryale path: no dossier by default, no local guards/rewrite/fallback."""
    scope = ConversationScopeKey(
        user_id=user_id,
        character_id=payload.character_id,
        conversation_id=payload.conversation_id,
    )
    max_turns = int(getattr(conversation_store, "max_turns", 8))
    primary = _primary_provider(router)
    rollback = RollbackTrace()
    started = perf_counter()

    if history_snapshot is not None:
        history = list(history_snapshot)
    else:
        history = await _snapshot_history(conversation_store, scope)

    async def _generate(messages: list[MessageInput]) -> ModelResponse:
        request = ModelRequest(
            route=Route.FAST_CHAT,
            character_id=payload.character_id,
            user_id=user_id,
            conversation_id=payload.conversation_id,
            messages=messages,
        )
        provider = primary
        if isinstance(primary, OpenAICompatibleProvider):
            provider = primary.clone(
                model=payload.model,
                temperature=payload.temperature,
                frequency_penalty=payload.frequency_penalty,
                max_tokens=payload.max_tokens,
                clamp_tokens=False,
                raw_errors=True,
            )
        # Primary only — never walk fallback_providers.
        return await provider.generate(request)

    async def _execute() -> TurnSuccess:
        nonlocal rollback
        if payload.persist:
            await conversation_store.append_user_message(scope, payload.message)
            # Re-read after append so trailing user is included once.
            live_history = await _snapshot_history(conversation_store, scope)
            # Drop trailing current user from history before rebuild (assemble style).
            if live_history and live_history[-1].content == payload.message:
                base_history = live_history[:-1]
            else:
                base_history = live_history
        else:
            base_history = history

        messages, system_label = _build_root_messages(
            system_mode=payload.system,
            custom_system=payload.custom_system,
            character_id=payload.character_id,
            history=base_history,
            current_message=payload.message,
        )
        history_messages = len([m for m in messages if m.role != "system"])
        memory = _memory_trace(history_messages=history_messages, max_turns=max_turns)

        sampling_provider = primary
        if isinstance(primary, OpenAICompatibleProvider):
            sampling_provider = primary.clone(
                model=payload.model,
                temperature=payload.temperature,
                frequency_penalty=payload.frequency_penalty,
                max_tokens=payload.max_tokens,
                clamp_tokens=False,
                raw_errors=True,
            )
        max_tokens, temperature = _provider_sampling(sampling_provider)

        try:
            response = await _generate(messages)
        except ProviderError as error:
            blocked = isinstance(error, ProviderUpstreamError) and error.blocked
            if payload.persist:
                rollback.attempted = True
                try:
                    ok = await conversation_store.pop_last_user_message_if_match(
                        scope, payload.message
                    )
                    rollback.succeeded = bool(ok)
                    if not ok:
                        memory = MemoryTrace(
                            lost=True,
                            detail="rollback did not remove trailing user turn",
                        )
                    else:
                        memory = MemoryTrace(
                            lost=False,
                            detail="trailing user turn rolled back",
                        )
                except Exception as rollback_error:  # noqa: BLE001
                    rollback.succeeded = False
                    memory = MemoryTrace(
                        lost=True,
                        detail=f"rollback failed: {type(rollback_error).__name__}",
                    )
            trace = OwnerTrace(
                channel="root",
                system=system_label,
                history_messages=history_messages,
                max_turns=max_turns,
                truncated=memory.lost and "max_turns" in (memory.detail or ""),
                max_tokens=max_tokens,
                temperature=temperature,
                provider=getattr(sampling_provider, "name", None),
                model=getattr(sampling_provider, "model", None),
                local_guard=LocalGuardTrace(triggered=False, bypass=True),
                fallback=FallbackTrace(configured=False, used=False),
                rewrite=RewriteTrace(applied=False, ops=[]),
                latency_ms=round((perf_counter() - started) * 1000),
                rollback=rollback,
                memory=memory,
                blocked=blocked,
            )
            failure = TurnFailure(
                trace=trace,
                error=error,
                detail=_failure_detail(error, channel="root", trace=trace),
            )
            error.owner_failure = failure  # type: ignore[attr-defined]
            raise

        if payload.persist:
            await conversation_store.append_assistant_message(scope, response.content)

        trace = OwnerTrace(
            channel="root",
            system=system_label,
            history_messages=history_messages,
            max_turns=max_turns,
            truncated=memory.lost,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=response.provider,
            model=response.model,
            local_guard=LocalGuardTrace(triggered=False, bypass=True),
            fallback=FallbackTrace(configured=False, used=False),
            rewrite=RewriteTrace(applied=False, ops=[]),
            latency_ms=round((perf_counter() - started) * 1000),
            retry_count=0,
            rollback=rollback,
            memory=memory,
            finish_reason=response.finish_reason,
        )
        return TurnSuccess(content=response.content, trace=trace)

    if payload.persist:
        async with conversation_store.transaction(scope):
            return await _execute()
    return await _execute()


def build_compare_diff(
    *,
    usuario_trace: OwnerTrace | None,
    root_trace: OwnerTrace | None,
    root_system: str,
) -> dict[str, Any]:
    def side(trace: OwnerTrace | None, *, default_system: str) -> dict[str, Any]:
        if trace is None:
            return {
                "system": default_system,
                "history": None,
                "max_tokens": None,
                "provider": None,
                "model": None,
                "local_guard": None,
                "fallback": None,
                "rewrite": None,
            }
        return {
            "system": trace.system,
            "history": trace.history_messages,
            "max_tokens": trace.max_tokens,
            "provider": trace.provider,
            "model": trace.model,
            "local_guard": (
                "bypass"
                if trace.local_guard.bypass
                else {
                    "triggered": trace.local_guard.triggered,
                    "reason": trace.local_guard.reason,
                }
            ),
            "fallback": trace.fallback.used if trace.channel == "usuario" else False,
            "rewrite": trace.rewrite.applied,
        }

    u = side(usuario_trace, default_system="bardera")
    r = side(root_trace, default_system=root_system)
    return {
        "system": {"usuario": u["system"], "root": r["system"]},
        "history": {"usuario": u["history"], "root": r["history"]},
        "max_tokens": {"usuario": u["max_tokens"], "root": r["max_tokens"]},
        "provider": {"usuario": u["provider"], "root": r["provider"]},
        "model": {"usuario": u["model"], "root": r["model"]},
        "local_guard": {"usuario": u["local_guard"], "root": r["local_guard"]},
        "fallback": {"usuario": u["fallback"], "root": r["fallback"]},
        "rewrite": {"usuario": u["rewrite"], "root": r["rewrite"]},
    }


async def run_compare(
    *,
    router: ModelRouter,
    conversation_store: ConversationStore,
    user_id: str,
    payload: OwnerConsoleChatRequest,
) -> dict[str, Any]:
    """Run usuario + root on the same frozen history. Never persists either side."""
    scope = ConversationScopeKey(
        user_id=user_id,
        character_id=payload.character_id,
        conversation_id=payload.conversation_id,
    )
    snapshot = await _snapshot_history(conversation_store, scope)

    # Force non-persist for compare regardless of payload.persist.
    usuario_payload = payload.model_copy(update={"persist": False})
    root_payload = payload.model_copy(update={"persist": False})

    async def _usuario() -> TurnSuccess | TurnFailure:
        try:
            return await run_usuario_turn(
                router=router,
                conversation_store=conversation_store,
                user_id=user_id,
                payload=usuario_payload,
                persist=False,
                history_snapshot=snapshot,
            )
        except ProviderError as error:
            failure = getattr(error, "owner_failure", None)
            if isinstance(failure, TurnFailure):
                return failure
            trace = OwnerTrace(channel="usuario", system="bardera", blocked=True)
            return TurnFailure(
                trace=trace,
                error=error,
                detail=_failure_detail(error, channel="usuario", trace=trace),
            )

    async def _root() -> TurnSuccess | TurnFailure:
        try:
            return await run_root_turn(
                router=router,
                conversation_store=conversation_store,
                user_id=user_id,
                payload=root_payload,
                history_snapshot=snapshot,
            )
        except ProviderError as error:
            failure = getattr(error, "owner_failure", None)
            if isinstance(failure, TurnFailure):
                return failure
            trace = OwnerTrace(
                channel="root",
                system=payload.system.value,
                local_guard=LocalGuardTrace(bypass=True),
                blocked=isinstance(error, ProviderUpstreamError) and error.blocked,
            )
            return TurnFailure(
                trace=trace,
                error=error,
                detail=_failure_detail(error, channel="root", trace=trace),
            )

    usuario_result, root_result = await asyncio.gather(_usuario(), _root())

    usuario_trace = (
        usuario_result.trace
        if isinstance(usuario_result, (TurnSuccess, TurnFailure))
        else None
    )
    root_trace = (
        root_result.trace if isinstance(root_result, (TurnSuccess, TurnFailure)) else None
    )

    return {
        "usuario": {
            "content": usuario_result.content if isinstance(usuario_result, TurnSuccess) else None,
            "owner": usuario_trace.to_dict() if usuario_trace else None,
        },
        "root": {
            "content": root_result.content if isinstance(root_result, TurnSuccess) else None,
            "owner": root_trace.to_dict() if root_trace else None,
        },
        "diff": build_compare_diff(
            usuario_trace=usuario_trace,
            root_trace=root_trace,
            root_system=payload.system.value,
        ),
        "errors": {
            "usuario": (
                usuario_result.detail if isinstance(usuario_result, TurnFailure) else None
            ),
            "root": root_result.detail if isinstance(root_result, TurnFailure) else None,
        },
    }
