/**
 * Per-browser-session conversation handle.
 *
 * Generates one opaque conversation handle per browser tab session. A page
 * refresh keeps it; the authenticated backend derives the actor identity.
 *
 * It is a resource identifier only, never an actor identity.
 */

const CONVERSATION_STORAGE_KEY = "rq.conversation_id";
const LEGACY_CONVERSATION_STORAGE_KEY = "cs.conversation_id";
const PREAUTH_USER_STORAGE_KEY = "rq.preauth_user_id";
const CLIENT_SCOPE_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isClientScopeId(value: string): boolean {
  return CLIENT_SCOPE_ID_PATTERN.test(value);
}

function generateId(): string {
  // randomUUID requires a secure context in browsers. getRandomValues is
  // the secure fallback for deployments where that convenience API is not
  // exposed. Prototype scopes fail closed if Web Crypto is unavailable.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  throw new Error("Secure random identifiers are unavailable.");
}

/**
 * Returns the conversation id for the current browser session.
 * Creates and stores it on first access; reuses on subsequent calls
 * and across page refreshes within the same tab.
 */
function getSessionId(
  storageKey: string,
  ssrPlaceholder: string,
  memoryKey: "conversation" | "preauth_user",
  legacyStorageKey?: string,
): string {
  if (typeof window === "undefined") {
    return ssrPlaceholder;
  }
  try {
    let id = sessionStorage.getItem(storageKey);
    if (id && !isClientScopeId(id)) {
      sessionStorage.removeItem(storageKey);
      id = null;
    }
    if (!id && legacyStorageKey) {
      id = sessionStorage.getItem(legacyStorageKey);
      if (id && isClientScopeId(id)) {
        sessionStorage.setItem(storageKey, id);
        sessionStorage.removeItem(legacyStorageKey);
      } else if (id) {
        sessionStorage.removeItem(legacyStorageKey);
        id = null;
      }
    }
    if (!id) {
      id = generateId();
      sessionStorage.setItem(storageKey, id);
    }
    return id;
  } catch {
    return getInMemoryId(memoryKey);
  }
}

const inMemoryIds: { conversation: string | null; preauth_user: string | null } = {
  conversation: null,
  preauth_user: null,
};

function getInMemoryId(key: "conversation" | "preauth_user"): string {
  const existing = inMemoryIds[key];
  if (existing) return existing;
  const generated = generateId();
  inMemoryIds[key] = generated;
  return generated;
}

/** Stable conversation handle for this browser tab session. */
export function getConversationId(): string {
  return getSessionId(
    CONVERSATION_STORAGE_KEY,
    "ssr-conversation",
    "conversation",
    LEGACY_CONVERSATION_STORAGE_KEY,
  );
}

/**
 * Pre-auth browser scope only. Used when NEXT_PUBLIC_AUTH_ENABLED=false.
 * Never a durable identity: Auth0-derived UUID replaces this when auth is on.
 */
export function getPreAuthUserId(): string {
  return getSessionId(PREAUTH_USER_STORAGE_KEY, "ssr-preauth-user", "preauth_user");
}
