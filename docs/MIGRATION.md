# RiotQueens — MIGRATION (plan nuevo)

**Autoridad:** [`../RIOTQUEENS_BIGPICKLE.md`](../RIOTQUEENS_BIGPICKLE.md) · [`AUTHORITY.md`](AUTHORITY.md)  
**Destino:** repo clean `https://github.com/Rybjuani/riotqueens`  
**Cantera (solo lectura):** `/home/rybjuani/Escritorio/RiotQueens-worktree`  
**No ejecutar:** `RIOTQUEENS_MIGRATION_VPS.md` del repo viejo (referencia histórica).

## Reglas del ejecutor

1. Cortes **en orden**. Cada uno cierra con verificación.
2. No inventar producto, modelo ni infra. Bloqueo → Owner (Pickle §7).
3. Secretos fuera de Git. `runtime.env` por scp con modo `600`.
4. Push **solo en C6**, tras auditoría.
5. Layout de código: `apps/api` + `apps/web` (reversible; Pickle §6 describe qué pertenece, no obliga rename a `/web` ahora).

---

## C0 — Baseline documental limpio

| Paso | Detalle | Verificación |
|---|---|---|
| 0.1 | `docs/AUTHORITY.md`, `docs/ROADMAP.md`, `docs/MIGRATION.md` presentes | listado `/docs` = esos 3 + `canon/` |
| 0.2 | Basura documental → trash externo `_scratch_trash/riotqueens-clean-corte0/` (`docs/docs/`, `docs/adr/`, `DECISION_REGISTER`, canon `.md` legacy, `RIOTQUEENS_MIGRATION_VPS.md`) | no quedan en HEAD de trabajo |
| 0.3 | Traer `DossierBardera.md`, `docker-compose.yml`, PDFs a `docs/canon/` | archivos presentes |
| 0.4 | `README.md` mapa ~30 líneas | `wc -l` ~30; punteros a Pickle / AUTHORITY / MIGRATION |
| 0.5 | `rg -i gemini` en configs del repo → vacío o solo menciones de “DESCARTADO” en comentarios de contrato | sin rutas de runtime Gemini |

**Cierre C0:** árbol documental alineado a Pickle §6; `/apps` aún no auditado en profundidad.

---

## Arquitectura T1 (VPS + OpenRouter)

```
Browser → Caddy → web:3000 / api:8000
api → postgres + OpenRouter (sao10k/l3.3-euryale-70b)
       max_tokens 180–220 · temp ~0.9 · system = prompts/bardera.preset.md
T3 GPU (Vast/vLLM) = gated Owner; mismo adaptador openai-compatible.
```

Rotación de secretos Auth0/VPS: **al final** de la migración (Owner), no al inicio.

## C0.5 — Higiene secrets + scripts

| Paso | Detalle | Verificación |
|---|---|---|
| 0.5.1 | `.env` solo contrato `KEY=value` (sin preámbulo con secretos en claro) | modo `600`; sin prose de passwords |
| 0.5.2 | `scripts/` → trash externo | no en árbol de trabajo |
| 0.5.3 | `ops/` conservado (Caddy/SQL/deploy) | compose los monta |

## C1 — Voz Bardera + caps T1

| Paso | Detalle | Verificación |
|---|---|---|
| 1.1 | `prompts/bardera.preset.md` (≤~80 líneas, CLEAN §2.2); PDFs/Dossier **no** al LLM | archivo presente; API lo carga |
| 1.2 | Caps T1: `max_tokens` clamp 180–220 + `RIOTQUEENS_MODEL_MAX_TOKENS` en `.env` / example / compose | payload incluye `max_tokens` |
| 1.3 | Dockerfile API `COPY prompts`; modelo runtime `l3.3-euryale-70b` | build + env |
| 1.4 | Sin filtrar nombre técnico de modelo al usuario | review + test si existe |

**Cierre C1:** preset único; caps T1 cableados.

---

## C2 — Stack local

| Paso | Detalle | Verificación |
|---|---|---|
| 2.1 | `docker compose up --build` local; migraciones SQL | landing `:80` 200 + `/api/health` ok |
| 2.2 | Chat Bardera vía OpenRouter `l3.3-euryale-70b` + caps | respuesta corta con voz; sin leak de provider |
| 2.3 | `ops/` (Caddy/SQL/deploy) ya cableado por compose | sin traer `scripts/` ni basura |
| 2.4 | Web Dockerfile standalone (`apps/web`, npm) — ya no monorepo pnpm | build web OK |

**Notas C2 (2026-08-27):** smoke local usó override `RIOTQUEENS_AUTH_ENABLED=false` solo para curl sin JWT; `.env` sigue con Auth0 on para C3 VPS. Timeout modelo subido a `60s` (5s mataba Euryale). Respuestas smoke: cortas, sin Gemini/OpenRouter en texto.

**Cierre C2:** stack reproducible en local.

---

## C3 — VPS

| Paso | Detalle | Verificación |
|---|---|---|
| 3.1 | SSH `~/.ssh/luxriot_vps`; layout `/opt/riotqueens/{releases,shared,current}` | acceso key-only |
| 3.2 | Release clean rsync **sin** `.env`; `shared/runtime.env` modo `600` + symlink | sin secretos en release |
| 3.3 | `ops/deploy.sh` (health wait + `ON_ERROR_STOP`); compose project `riotqueens` | postgres volume conservado |
| 3.4 | Smoke por IP: landing + `/api/health` + runtime Euryale; chat sin JWT → 401 | Auth on |
| 3.5 | Provider smoke in-container: Bardera corta + `max_tokens=200` | sin leak Gemini/OpenRouter |

**Hecho (2026-08-27):**
- Release: `/opt/riotqueens/releases/clean-20260827-155443` ← `current`
- Rollback: `cd /opt/riotqueens/releases/cc95e75 && sudo docker compose up -d` (+ restaurar `shared/runtime.env.bak.pre-clean-*` si hace falta)
- `POSTGRES_PASSWORD` del VPS se conserva desde backup shared (no pisar con laptop)
- Auth0 **callbacks** aún son acción Owner (C5): agregar `http://148.113.167.121` / `/auth/callback` en el dashboard Auth0 para login UI completo

**Cierre C3:** VPS sirviendo el clean con puente Euryale + Auth API on.

---

## C4 — GPU (GATED Owner)

Vast.ai RTX 4090 spot + modelo T3 del Pickle §3. No arrancar sin tope de gasto y OK del Owner.

---

## C5 — Dominio + TLS + Auth0 (completado)

| Paso | Detalle | Verificación |
|---|---|---|
| 5.1 | Auth0: URLs `https://riotqueens.live` (+ IP whitelisted) | dashboard Auth0 |
| 5.2 | Caddy: `/api/v1/*` + `/api/health` → API; **resto** (incl. `/api/token`) → web | `/api/token` sin sesión = 401 Next |
| 5.3 | Token route Auth0 v4: `getAccessToken()` | rebuild web |
| 5.4 | DNS A `@` → VPS; site `https://riotqueens.live` (sin www) | propagado |
| 5.5 | Caddy TLS Let’s Encrypt; `SITE_ADDRESS` + `APP_BASE_URL` = `https://riotqueens.live` | candado verde |
| 5.6 | Login `/auth/login` → Auth0 con `redirect_uri=https://riotqueens.live/auth/callback` | 307 + smoke Owner |

**Cierre C5 (2026-08-27):** dominio `riotqueens.live` + HTTPS (Caddy) + Auth0 https whitelisted. Smoke Owner: login + chat OK.

---

## C-API-NUCLEAR — Rebuild `apps/api` sin cape Codex (2026-08-27)

**Motivo:** CLEAN §1 — no capear Bardera. El API Codex (~3.5k LOC + ~4k tests) sustituía refusals/bloqueos por `SAFE_FALLBACK` / continuity. Los “15k archivos” del tar viejo eran casi todo `.venv`+`node_modules`.

| Paso | Detalle | Verificación |
|---|---|---|
| N.1 | API Codex → trash `riotqueens-api-codex-*` | referencia, no borrar aún |
| N.2 | API nuevo: chat + health + Auth0/clickwrap + convos PG; **sin** memories; **sin** OutputValidator-cape | tests `test_nuclear_api.py` |
| N.3 | Router: primary → fallback → error honesto; nunca inventar voz | “No puedo ayudar…” no se reescribe |
| N.4 | Smoke local | `"bien, bobo"` + caps |
| N.5 | Cutover VPS: rebuild solo `api` (web intacto) | health + Auth0 flow Owner |

**Conservado:** `apps/web`, preset, `max_tokens`, migraciones SQL, Caddy fix `/api/token`.

---

## C6 — Auditoría y push

| Paso | Detalle | Verificación |
|---|---|---|
| 6.1 | Auditoría del diff acumulado | checklist AUTHORITY |
| 6.2 | Primer push a `Rybjuani/riotqueens` con OK Owner | `git remote -v` |

**Hecho (2026-08-27):** primer commit limpio — API nuclear sin cape, web + Auth0/Caddy, preset, docs canon PDFs, sin `.env`/`.venv`. Gemini solo como anti-leak/DESCARTADO.

---

## Owner Console (API) — test Euryale crudo

**Deploy prod (2026-08-28):** release `clean-20260828-012200` ← `current`; API rebuild; `RIOTQUEENS_OWNER_AUTH0_SUBJECTS` seteado en `shared/runtime.env` (modo 600). Smoke: `/api/health` 200, `owner_console_configured=true`, `/v1/root/chat` sin JWT → 401.

Endpoints Owner-only (chat público `/v1/chat` intacto):

| Path | Qué hace |
|---|---|
| `POST /v1/usuario/chat` | Pipeline prod + telemetría `owner` |
| `POST /v1/root/chat` | Sin dossier por defecto (`system=empty\|bardera\|custom`); sin fallback/anti-leak/rewrite; cartel crudo OpenRouter en error |
| `POST /v1/compare` | Mismo input → usuario+root + `diff`; no persiste |

Gate fail-closed: `RIOTQUEENS_OWNER_AUTH0_SUBJECTS` (prod) / `RIOTQUEENS_OWNER_USER_IDS` (auth off). Sin UI todavía.

Smoke local (auth off):

```bash
# RIOTQUEENS_AUTH_ENABLED=false RIOTQUEENS_OWNER_USER_IDS=smoke
curl -s localhost:8000/v1/root/chat -H 'content-type: application/json' \
  -d '{"character_id":"bardera","conversation_id":"root1","user_id":"smoke","message":"hola","system":"empty"}'
curl -s localhost:8000/v1/compare -H 'content-type: application/json' \
  -d '{"character_id":"bardera","conversation_id":"root1","user_id":"smoke","message":"hola","system":"empty"}'
```

---

## Pendiente próximo agente

- **Rotación de claves** — la hace el Owner al final; no tocar secretos ahora.
- **Preset v2 denso** — construir con material RAW que provea el Owner.
- **Dossiers oficiales de las 6 queens** — Owner provee guiones + glosario + modismos.
- **Polish legal (textos públicos)** — reemplazar alcohol/droga por naranju/manaos.
- **Regla de preset** — insinuar, jamás afirmar (no vender lo que no existe).
- **Slogan Bardera** — `"TE BARDEA. TE BANCA. SE QUEDA."` (no “te quiere”).
- **Owner Console UI** — reutilizar contratos `/v1/usuario` `/v1/root` `/v1/compare` cuando haga falta.

---

## Fuera de alcance (no abrir sin Owner)

- Nuevas Queens en runtime más allá de Bardera.
- Features de producto no pedidas.
- Recuperar material del trash o del worktree viejo “porque estaba”.
- SKILLS de programación del experimento dentro del preset (Pickle §6).
