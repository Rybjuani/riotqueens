# RiotQueens.ai

Experiencia `+18` de Queens virtuales ficticias. Complejidad escondida; Queen al frente.

## Autoridad

1. [`RIOTQUEENS_BIGPICKLE.md`](RIOTQUEENS_BIGPICKLE.md) — verdad del repo
2. [`docs/AUTHORITY.md`](docs/AUTHORITY.md) — reglas para agentes
3. [`docs/ROADMAP.md`](docs/ROADMAP.md) — puntero al Pickle
4. [`docs/MIGRATION.md`](docs/MIGRATION.md) — plan por cortes

Cantera de lectura (no autoridad): `RiotQueens-worktree` en el Escritorio.

## Layout

- `apps/api` — FastAPI + provider OpenAI-compatible
- `apps/web` — landing + chat
- `prompts/` — preset Bardera (C1)
- `docs/canon/` — PDFs visuales (no van al prompt)
- `DossierBardera.md` — referencia humana de voz

## Levantar (local)

```bash
cp .env.example .env   # secretos solo acá; nunca en Git
docker compose up
```

Push recién en C6 tras auditoría (Pickle §7).
