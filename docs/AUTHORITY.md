# RiotQueens — AUTHORITY

**Repo:** `Rybjuani/riotqueens` (clean).  
**Cantera de lectura (no autoridad):** `/home/rybjuani/Escritorio/RiotQueens-worktree`

## Jerarquía (anti-contradicción)

1. **Owner** — producto, canon, gasto, aceptación.
2. **`RIOTQUEENS_BIGPICKLE.md`** (raíz) — verdad del repo: modelos, tiers, retención Bardera, repo clean, orden machete.
3. **Este archivo** — reglas operativas para agentes. En el repo limpio cumple el rol que el Pickle §0 atribuye a `AGENTS.md` (ese archivo no vive aquí).
4. **`docs/ROADMAP.md`** — puntero al Pickle (roadmap único).
5. **`docs/MIGRATION.md`** — plan ejecutable por cortes.
6. **Código + tests** — verifican lo implementado; no inventan producto.
7. **Repo viejo / trash / historial Git** — nunca autoridad de producto.

Si SPECT, ADRs, DECISION_REGISTER, handoffs o el `RIOTQUEENS_MIGRATION_VPS.md` viejo contradicen el Pickle → **manda el Pickle**.

## Reglas operativas mínimas

- Ejecutor sigue `docs/MIGRATION.md`; no decide producto, modelo ni infra. Si duda: no inventa, escala al Owner (Pickle §7).
- Secretos nunca en Git, logs ni chat. SSH key por path (`~/.ssh/luxriot_vps`), nunca en `.env`. `runtime.env` modo `600` por scp, nunca por Git.
- `rg -i gemini` debe quedar vacío en configs y runtime. Gemini descartado.
- Salida LLM = no confiable. Identidad, fallback y continuidad de cada Queen son server-owned.
- No nombrar el modelo técnico al usuario; lenguaje humanizado (Pickle §4).
- No agregar infraestructura por anticipado. GPU gated por Owner (Pickle §1–§3).
- Push recién tras auditoría del corte final (Pickle §7).
- Interfaz y copy público en español natural; código e identificadores en inglés.

## Qué no entra al HEAD limpio

Todo lo que no figure en Pickle §6 y no nombre el corte activo de `MIGRATION.md` → trash externo, no “por si acaso”.
