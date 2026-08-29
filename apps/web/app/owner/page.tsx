"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Mode = "usuario" | "root" | "compare";
type RootSystem = "empty" | "bardera";

type ConsoleMessage = {
  label: string;
  content: string;
};

class OwnerConsoleError extends Error {
  constructor(
    readonly status: number,
    readonly body: unknown,
  ) {
    super(`Owner Console request failed (${status})`);
    this.name = "OwnerConsoleError";
  }
}

const API_BASE = "http://127.0.0.1:8000";
const TOKEN_STORAGE_KEY = "riotqueens.owner-console.token";

function newConversationId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `owner-${crypto.randomUUID()}`;
  }
  return `owner-${Date.now().toString(36)}`;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function responseContent(value: unknown): string {
  const content = asRecord(asRecord(value).response).content;
  return typeof content === "string" ? content : "(Sin contenido de respuesta.)";
}

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

async function postOwner(
  path: string,
  token: string,
  payload: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token.replace(/^Bearer\s+/i, "").trim()}`,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const rawBody = await response.text();
  let body: unknown;
  try {
    body = rawBody ? JSON.parse(rawBody) : {};
  } catch {
    body = { text: rawBody };
  }
  if (!response.ok) throw new OwnerConsoleError(response.status, body);
  return asRecord(body);
}

export default function OwnerConsolePage() {
  const [token, setToken] = useState("");
  const [mode, setMode] = useState<Mode>("usuario");
  const [rootSystem, setRootSystem] = useState<RootSystem>("empty");
  const [conversationId, setConversationId] = useState(newConversationId);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ConsoleMessage[]>([]);
  const [trace, setTrace] = useState<unknown>(null);
  const [error, setError] = useState<unknown>(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    setToken(window.sessionStorage.getItem(TOKEN_STORAGE_KEY) ?? "");
  }, []);

  useEffect(() => {
    if (token) window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    else window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  }, [token]);

  const modeDescription = useMemo(() => {
    if (mode === "usuario") return "Pipeline público real, con memoria persistida y traza privada.";
    if (mode === "root") return "Ruta cruda: conserva el error upstream y permite elegir sistema vacío o Bardera.";
    return "Mismo mensaje por Usuario y Root; no persiste turnos para no contaminar el diagnóstico.";
  }, [mode]);

  const resetSession = () => {
    setConversationId(newConversationId());
    setMessages([]);
    setTrace(null);
    setError(null);
  };

  const clearToken = () => {
    setToken("");
    window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanMessage = message.trim();
    const cleanToken = token.replace(/^Bearer\s+/i, "").trim();
    if (!cleanMessage || !cleanToken || sending) return;

    setSending(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        character_id: "bardera",
        conversation_id: conversationId,
        message: cleanMessage,
        system: mode === "root" ? rootSystem : "bardera",
        persist: mode !== "compare",
      };
      const endpoint = mode === "compare" ? "/v1/compare" : `/v1/${mode}/chat`;
      const data = await postOwner(endpoint, cleanToken, payload);

      if (mode === "compare") {
        const usuario = asRecord(data.usuario);
        const root = asRecord(data.root);
        setMessages((current) => [
          ...current,
          { label: "VOS · COMPARE", content: cleanMessage },
          { label: "USUARIO", content: responseContent(usuario) },
          { label: "ROOT", content: responseContent(root) },
        ]);
        setTrace({
          usuario: usuario.owner ?? null,
          root: root.owner ?? null,
          diff: data.diff ?? null,
          errors: data.errors ?? null,
        });
      } else {
        setMessages((current) => [
          ...current,
          { label: "VOS", content: cleanMessage },
          { label: mode.toUpperCase(), content: responseContent(data) },
        ]);
        setTrace(data.owner ?? null);
      }
      setMessage("");
    } catch (caught) {
      setError(caught instanceof OwnerConsoleError ? caught.body : { message: "No se pudo conectar al túnel privado." });
    } finally {
      setSending(false);
    }
  };

  return (
    <main className="owner-console">
      <header className="owner-console__header">
        <div>
          <p className="label">PRIVATE LOOPBACK · OWNER ONLY</p>
          <h1>CONSOLA DE DIAGNÓSTICO</h1>
        </div>
        <span className="owner-console__status">127.0.0.1:3000 → 127.0.0.1:8000</span>
      </header>

      <section className="owner-console__notice">
        <p>
          Abrila sólo con ambos túneles SSH activos. El token de Auth0 queda únicamente en esta pestaña y nunca viaja
          por la ruta pública. Root puede mostrar el cartel crudo de OpenRouter.
        </p>
      </section>

      <section className="owner-console__controls" aria-label="Controles de Owner Console">
        <label>
          Token de sesión Auth0
          <input
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Pegalo una vez por pestaña"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button className="btn" type="button" onClick={clearToken} disabled={!token}>
          OLVIDAR TOKEN
        </button>
        <button className="btn" type="button" onClick={resetSession} disabled={sending}>
          HILO NUEVO
        </button>
      </section>

      <section className="owner-console__mode" aria-label="Modo de prueba">
        {(["usuario", "root", "compare"] as Mode[]).map((candidate) => (
          <button
            className={mode === candidate ? "owner-console__mode-active" : ""}
            key={candidate}
            onClick={() => setMode(candidate)}
            type="button"
          >
            {candidate.toUpperCase()}
          </button>
        ))}
        {mode === "root" && (
          <label className="owner-console__system">
            Sistema Root
            <select value={rootSystem} onChange={(event) => setRootSystem(event.target.value as RootSystem)}>
              <option value="empty">Vacío / crudo</option>
              <option value="bardera">Dossier Bardera</option>
            </select>
          </label>
        )}
        <p>{modeDescription}</p>
      </section>

      <section className="owner-console__grid">
        <div className="owner-console__chat">
          <div className="owner-console__thread" aria-live="polite" aria-busy={sending}>
            {messages.length === 0 && <p className="chat-empty">Elegí modo y hablá normal. El diagnóstico queda al costado.</p>}
            {messages.map((entry, index) => (
              <article className="owner-console__message" key={`${entry.label}-${index}`}>
                <span>{entry.label}</span>
                <p>{entry.content}</p>
              </article>
            ))}
            {sending && <p className="owner-console__sending">Consultando proveedor…</p>}
          </div>
          <form className="owner-console__composer" onSubmit={submit}>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Escribile a Bardera…"
              maxLength={4000}
              disabled={sending}
            />
            <button className="btn solid" type="submit" disabled={!message.trim() || !token.trim() || sending}>
              ENVIAR
            </button>
          </form>
        </div>

        <aside className="owner-console__trace">
          <h2>TRAZA PRIVADA</h2>
          <p>Provider, modelo, latencia, memoria, fallback y errores raw cuando correspondan.</p>
          {error !== null && (
            <div className="owner-console__error">
              <h3>ERROR</h3>
              <pre>{pretty(error)}</pre>
            </div>
          )}
          <pre>{trace ? pretty(trace) : "Esperando primer turno."}</pre>
        </aside>
      </section>
    </main>
  );
}
