/**
 * Typed client for the canonical FastAPI backend.
 * Public contract: POST /v1/chat → ChatResponse { response: { content } }
 *
 * Per Issue #3: the frontend is a client only. Chat must go through the
 * existing FastAPI backend (ModelRouter / Provider abstraction /
 * OutputValidator), not a second Next.js API route. The conversation_id
 * is a per-browser-session identifier (lib/session.ts), NOT a shared
 * constant. The client never sends a system prompt — the server owns
 * the canonical Queen personality.
 */

import { getConversationId, getPreAuthUserId } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";

/** Versions shown by the clickwrap UI; must match API package defaults. */
export const CONSENT_AGE_GATE_VERSION = "2026-08-09";
export const CONSENT_TERMS_VERSION = "2026-08-09";
export const CONSENT_PRIVACY_VERSION = "2026-08-09";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  response: {
    content: string;
  };
}

export class ChatApiError extends Error {
  constructor(readonly status: number, statusText: string) {
    super(`Chat API error: ${status} ${statusText}`);
    this.name = "ChatApiError";
  }
}

export interface ConsentStatus {
  accepted: boolean;
  required_age_gate_version: string;
  required_terms_version: string;
  required_privacy_version: string;
}

async function requestHeaders(): Promise<HeadersInit> {
  if (!AUTH_ENABLED) {
    return { "Content-Type": "application/json" };
  }
  const tokenResponse = await fetch("/api/token", { cache: "no-store" });
  if (!tokenResponse.ok) throw new Error("Authentication required");
  const { accessToken } = (await tokenResponse.json()) as { accessToken: string };
  return { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` };
}

function scopeFields(): { user_id?: string; conversation_id: string } {
  if (AUTH_ENABLED) {
    return { conversation_id: getConversationId() };
  }
  return {
    user_id: getPreAuthUserId(),
    conversation_id: getConversationId(),
  };
}

/**
 * Send a single chat message to the canonical Queen.
 * The backend keeps conversation state server-side; the frontend sends
 * one message at a time per the existing ChatRequest contract.
 */
export async function sendChat(
  message: string,
  opts?: { character_id?: string; signal?: AbortSignal },
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/v1/chat`, {
    method: "POST",
    headers: await requestHeaders(),
    body: JSON.stringify({
      message,
      character_id: opts?.character_id ?? "bardera",
      ...scopeFields(),
    }),
    signal: opts?.signal,
  });

  if (!res.ok) {
    throw new ChatApiError(res.status, res.statusText);
  }

  return (await res.json()) as ChatResponse;
}

/**
 * Clear the server-side conversation history for the current browser
 * session. This is the visible reset action — it does NOT clear other
 * users' conversations, other characters, or other conversation ids.
 *
 * The server returns `{deleted: bool, conversation_id: string}`.
 * `deleted=false` simply means there was no in-process state for this
 * scope yet (e.g. a fresh browser tab), which is not an error.
 *
 * Note: with DATABASE_URL the API persists conversations in PostgreSQL;
 * without it the API uses in-process prototype state only.
 */
export async function clearConversation(
  opts?: { character_id?: string; signal?: AbortSignal },
): Promise<{ deleted: boolean; conversation_id: string }> {
  const scope = scopeFields();
  const res = await fetch(
    `${API_URL}/v1/conversations/${encodeURIComponent(scope.conversation_id)}`,
    {
      method: "DELETE",
      headers: await requestHeaders(),
      body: JSON.stringify({
        character_id: opts?.character_id ?? "bardera",
        ...(scope.user_id ? { user_id: scope.user_id } : {}),
      }),
      signal: opts?.signal,
    },
  );
  if (!res.ok) {
    throw new Error(`Clear conversation API error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as { deleted: boolean; conversation_id: string };
}

/**
 * Load the server-side conversation history for the current browser
 * session. The visible chat uses it on mount and to reconcile sends.
 * Returns stored user/assistant messages only — the canonical Queen
 * system prompt is NEVER stored and NEVER returned.
 */
export interface ConversationMessageView {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationSummary {
  user_id: string;
  character_id: string;
  conversation_id: string;
  messages: ConversationMessageView[];
  created_at: string;
  updated_at: string;
}

export async function getConversation(
  opts?: { character_id?: string; signal?: AbortSignal },
): Promise<ConversationSummary> {
  const scope = scopeFields();
  const params = new URLSearchParams({
    character_id: opts?.character_id ?? "bardera",
  });
  if (scope.user_id) params.set("user_id", scope.user_id);
  const res = await fetch(
    `${API_URL}/v1/conversations/${encodeURIComponent(scope.conversation_id)}?${params.toString()}`,
    { signal: opts?.signal, cache: "no-store", headers: await requestHeaders() },
  );
  if (!res.ok) {
    throw new Error(`Get conversation API error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as ConversationSummary;
}

export async function getConsentStatus(signal?: AbortSignal): Promise<ConsentStatus> {
  if (!AUTH_ENABLED) {
    return {
      accepted: true,
      required_age_gate_version: CONSENT_AGE_GATE_VERSION,
      required_terms_version: CONSENT_TERMS_VERSION,
      required_privacy_version: CONSENT_PRIVACY_VERSION,
    };
  }
  const res = await fetch(`${API_URL}/v1/consent/status`, {
    signal,
    cache: "no-store",
    headers: await requestHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Consent status error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as ConsentStatus;
}

export async function acceptConsent(body: {
  age_confirmed: boolean;
  age_gate_version: string;
  terms_version: string;
  privacy_version: string;
}): Promise<void> {
  const res = await fetch(`${API_URL}/v1/consent/accept`, {
    method: "POST",
    headers: await requestHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Consent accept error: ${res.status} ${res.statusText}`);
  }
}
