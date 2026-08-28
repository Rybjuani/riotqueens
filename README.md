# RiotQueens.ai

Experiencia `+18` de Queens virtuales ficticias. Complejidad escondida; Queen al frente.

**Prod:** `https://riotqueens.live` (Caddy TLS → web + `/api/*`).

## Autoridad

1. [`RIOTQUEENS_BIGPICKLE.md`](RIOTQUEENS_BIGPICKLE.md) — verdad del repo
2. [`docs/AUTHORITY.md`](docs/AUTHORITY.md) — reglas para agentes
3. [`docs/ROADMAP.md`](docs/ROADMAP.md) — puntero al Pickle
4. [`docs/MIGRATION.md`](docs/MIGRATION.md) — plan por cortes + Owner Console

Cantera de lectura (no autoridad): `RiotQueens-worktree` en el Escritorio.

## Layout

- `apps/api` — FastAPI nuclear: chat público + Owner Console + Auth0/clickwrap + conversaciones PG
- `apps/web` — landing + chat Bardera (cliente; no llama al LLM directo)
- `prompts/` — preset Bardera (único system del canal usuario)
- `docs/canon/` — PDFs visuales (no van al prompt)
- `ops/` — Caddy, deploy, migraciones SQL
- `DossierBardera.md` — referencia humana de voz (no runtime)

## Chat público vs Owner Console

| Canal | Paths | Quién |
|---|---|---|
| Público | `POST /v1/chat` | usuarios Auth0 + clickwrap; preset Bardera; errors sanitizados |
| Owner | `POST /v1/usuario/chat`, `/v1/root/chat`, `/v1/compare` | allowlist Auth0 `sub`; root/compare para testear Euryale crudo |

Detalle y smoke: [`docs/MIGRATION.md`](docs/MIGRATION.md) § Owner Console.

## Levantar (local)

```bash
cp .env.example .env   # secretos solo acá; nunca en Git
docker compose up --build
```

Owner Console local (auth off): setear `RIOTQUEENS_OWNER_USER_IDS` en `.env`.  
Prod: `RIOTQUEENS_OWNER_AUTH0_SUBJECTS` solo en `shared/runtime.env` (modo `600`).
