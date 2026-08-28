# RiotQueens.ai

Experiencia `+18` de Queens virtuales ficticias. Complejidad escondida; Queen al frente.

**Prod:** `https://riotqueens.live` (Caddy TLS → web + `/api/*` público).

## Autoridad (mapa)

1. [`AGENTS.md`](AGENTS.md) — gobernanza operacional (LEY 0, deploy, seguridad, providers)
2. [`DOSSIER_MAESTRO.md`](DOSSIER_MAESTRO.md) — canon / persona / casting (runtime carga el archivo completo)
3. Este `README.md` — mapa técnico **no autoritativo**

Forense sin autoridad: [`_trash_scratch/`](_trash_scratch/).

## Layout

- `apps/api` — FastAPI: chat público + Owner Console (loopback/SSH) + Auth0/clickwrap + conversaciones PG
- `apps/web` — landing + chat Bardera
- `DOSSIER_MAESTRO.md` — system prompt / persona (completo)
- `docs/canon/` — PDFs visuales (no van al prompt)
- `ops/` — Caddy, `deploy.sh`, `release.sh` (`git archive` + manifiesto SHA-256), migraciones SQL

## Chat público vs Owner Console

| Canal | Paths | Quién / cómo |
|---|---|---|
| Público | `POST /v1/chat`, consent, conversations | usuarios Auth0 + clickwrap; Caddy `/api/v1/...` |
| Owner | `POST /v1/usuario/chat`, `/v1/root/chat`, `/v1/compare` | allowlist; **no** expuesto por Caddy; `ssh -L 8000:127.0.0.1:8000 ubuntu@VPS` |

Detalle operacional: [`AGENTS.md`](AGENTS.md).

## Levantar (local)

```bash
cp .env.example .env   # secretos solo acá; nunca en Git
docker compose up --build
```

Owner Console local: API en `127.0.0.1:8000`. Setear `RIOTQUEENS_OWNER_USER_IDS` con auth off.  
Prod: `RIOTQUEENS_OWNER_AUTH0_SUBJECTS` solo en `shared/runtime.env` (modo `600`).

## Release (LEY 0)

```bash
./ops/release.sh HEAD   # requiere push autorizado a origin/main
```
