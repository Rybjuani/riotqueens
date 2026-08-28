# RiotQueens — ROADMAP

**Autoridad operacional:** [`../AGENTS.md`](../AGENTS.md)  
**Persona / casting:** [`../DOSSIER_MAESTRO.md`](../DOSSIER_MAESTRO.md)

Este archivo es un puntero. Si diverge de `AGENTS.md`, **manda `AGENTS.md`**.

## Resumen operativo

| Prioridad | Qué | Fuente |
|---|---|---|
| 1º | Cerrar Vast.ai + Auth0 (pendiente = burn) | AGENTS.md |
| 2º | LEY 0: LOCAL == GITHUB == VPS vía `ops/release.sh` | AGENTS.md §8 |
| T1 | Euryale 70B vía OpenRouter; `max_tokens` band 180–220 (valor actual 200) | AGENTS.md §3 |
| T2 | Multimodal — **no inventar nombre de modelo** | AGENTS.md §3 |
| T3 | Qwen3.8-27B Uncensored en Vast.ai 4090 spot — **gated Owner** | AGENTS.md §3 |
| Bardera | Dossier Maestro completo; “te quiero” rareza contextual Nivel 1 | DOSSIER_MAESTRO.md |
| Owner | Console en loopback + SSH tunnel (no Caddy público) | AGENTS.md §5–§6 |

## Ejecución

Cortes históricos: [`MIGRATION.md`](MIGRATION.md) (evidencia de plan; no reabre decisiones).  
Prod: `https://riotqueens.live`.
