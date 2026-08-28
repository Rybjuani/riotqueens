# RiotQueens — Plan de migración al VPS

**Versión:** 1.0 · **Fecha:** 2026-08-23
**Autoridad:** [`RIOTQUEENS_BIGPICKLE.md`](RIOTQUEENS_BIGPICKLE.md) (ADR BP-0001 ratificado por el Owner el 2026-08-23) · `SPECT.md` · `AGENTS.md`
**Ejecutor asignado:** Codex (ejecutor, no decisor)
**Alcance:** mudar el repo limpio al VPS OVH VPS-2 (Beauharnois, CA — actual preprod `148.113.167.121`), eliminar Gemini de todo runtime, dejar el puente cloud Euryale operativo y dejar preparada la fase GPU gated por OWNER_INVESTIGATION (P1).

## Reglas para el ejecutor

1. Ejecutar los cortes **en orden**. Cada corte termina con su verificación y evidencia en `docs/migration/LOG.md` (crear al iniciar; comando + salida resumida, sin secretos).
2. Prohibido introducir decisiones de producto, modelo, pricing, canon o infraestructura no documentadas aquí. Cualquier desviación o bloqueo → **detener y escalar al Owner**, no improvisar.
3. Commits convencionales por corte (`docs:`, `chore:`, `fix:`, `feat:`). **Push sólo en el Corte 6**, previa auditoría del diff.
4. Secretos jamás en Git, logs ni handoffs. El `.env` real viaja al VPS por scp/rsync con permisos `600`, nunca por el repo.
5. No borrar nada del VPS antes de que el nuevo stack esté verificado; conservar rollback en cada corte.

---

## Corte 0 — Preparación local (pre-vuelo)

| Paso | Detalle | Verificación |
|---|---|---|
| 0.1 | Crear rama `migracion/vps-limpieza` desde el estado actual del worktree | `git branch --show-current` |
| 0.2 | Confirmar baseline ya saneado: FIX MEMORIA revertido, tipografía Owner conservada, `.gitignore` ampliado | `pytest` 178/178 · `ruff` limpio · `pnpm --filter web lint && build` |

**Estado al cierre:** baseline verde en rama de migración.

## Corte 1 — Higiene documental post-ratificación

| Paso | Detalle | Verificación |
|---|---|---|
| 1.1 | `README.md`: quitar fila del handoff en "Mapa único de trabajo", reemplazar la sección de laboratorio/proveedores (referenciaba `PROVIDER_LAB.md`) y las referencias a casting cerrado/Gemini por punteros a ADR BP-0001 | `rg -n "PROVIDER_LAB\|HANDOFF_ORGANIZADO\|casting-matrix" README.md docs/ apps/` → vacío |
| 1.2 | `SPECT.md` v0.3 → v0.4: §8 casting cerrado queda derogado por ADR BP-0001; actualizar estado verificado del proveedor (Gemini eliminado, puente Euryale transitorio) | diff revisable, versión y fecha actualizadas |
| 1.3 | `AGENTS.md`: agregar BIGPICKLE a la lista de Autoridad; reemplazar "handoff vigente" del control de macrofase por BIGPICKLE | lectura directa |
| 1.4 | `docs/DECISION_REGISTER.md`: anotar derogaciones como registro histórico (no borrar entradas viejas; es registro, no autoridad viva) | coherencia con BIGPICKLE §3 |
| 1.5 | Commit `docs: ratificar BIGPICKLE y sanear documentación legacy` | `git log --oneline -1` |

**Estado al cierre:** cero referencias rotas a archivos movidos; docs alineadas a decisiones ratificadas.

## Corte 2 — Contrato de entorno

| Paso | Detalle | Verificación |
|---|---|---|
| 2.1 | Validar el nuevo contrato `.env.example` contra `docker compose up` local en modo mock (sin claves) | landing carga, `/health` OK, chat Bardera responde en modo mock |
| 2.2 | Preparar `runtime.env` para el VPS a partir del contrato: `RIOTQUEENS_MODEL_PROVIDER=openai` + `BASE_URL=https://openrouter.ai/api/v1` + `NAME=sao10k/l3.3-euryale-70b` (puente primario), fallback vacío (= mock interno como degradación), flags de auth como en preprod actual hasta tener dominio. Sin ninguna variable Gemini/Groq/HF/Ollama | `rg -i gemini runtime.env` → vacío · permisos 600 |

**Estado al cierre:** entorno reproducible local y listo para transferir.

## Corte 3 — Repo y servicios en el VPS

| Paso | Detalle | Verificación |
|---|---|---|
| 3.1 | Acceso SSH al VPS con clave; usuario deploy no-root; directorio dedicado `/opt/riotqueens` | `ssh` sin password, `ls /opt/riotqueens` |
| 3.2 | Transferir repo (bundle git o rsync excluyendo `.env*`, node_modules, tarballs) y `runtime.env` vía scp | hash del bundle coincidente |
| 3.3 | `docker compose build && up -d`; aplicar migraciones SQL idempotentes existentes y verificar esquema | contenedores healthy · tablas verificadas |
| 3.4 | Revisar `ops/deploy.sh` (hoy untracked): confirmar `ON_ERROR_STOP`, timeouts, idempotencia; recién entonces trackearlo | script revisado línea a línea |
| 3.5 | Caddy HTTP por IP: smoke de `/health`, landing, chat Bardera `mode=real` vía puente Euryale (verificar respuesta con voz Bardera y sin filtración de proveedor) | capturas/salidas en LOG.md |
| 3.6 | Confirmar ausencia total de Gemini en configs y runtime del VPS | `rg -i gemini` en configs → vacío |
| 3.7 | Rollback disponible: release anterior (7448898) preservada hasta cerrar Corte 5 | procedimiento de vuelta escrito en LOG.md |

**Estado al cierre:** VPS sirviendo el código limpio con puente Euryale.

## Corte 4 — Fase GPU (GATED por el Owner)

**Gate previo: P1 = OWNER_INVESTIGATION.** El Owner investiga LLM local compatible con Bardera (open source + unrestricted + multimodal). Este corte NO arranca sin su decisión explícita.

| Paso | Detalle |
|---|---|
| 4.1 | Instancia GPU spot (Vast.ai o RunPod, RTX 4090 inicial): apagado automático en idle, tope de gasto diario definido por el Owner |
| 4.2 | Stack vLLM expuesto como API OpenAI-compatible; modelo según decisión P1 |
| 4.3 | Benchmark de voz Bardera con el método vigente (sin pagar contexto completo por eval): batería local sanitizada, criterios `hard_fails` / `capability_boundaries` / `infra_failures` |
| 4.4 | Si pasa: apuntar `RIOTQUEENS_MODEL_BASE_URL` del VPS al pod GPU; el puente Euryale queda como fallback |

## Corte 5 — Dominio, TLS y Auth0 (gates externos conocidos)

Requiere acciones del Owner marcadas como [OWNER].

| Paso | Responsable |
|---|---|
| 5.1 [OWNER] Registrar dominio `riotqueens.ai` | Owner |
| 5.2 DNS A → `148.113.167.121`; Caddy emite TLS automático; `SITE_ADDRESS=riotqueens.ai` | Codex tras 5.1 |
| 5.3 Actualizar callbacks/origins en Auth0 CA; hacer flip conjunto de `RIOTQUEENS_AUTH_ENABLED=true` y `NEXT_PUBLIC_AUTH_ENABLED=true` | Codex tras 5.2 |
| 5.4 Smoke completo: login → clickwrap (age gate + términos + privacidad versionados) → chat Bardera autenticado → logout | evidencia en LOG.md |

## Corte 6 — Cierre: push final

| Paso | Detalle | Verificación |
|---|---|---|
| 6.1 | Auditoría integral del diff acumulado (Owner o BigPickle con evidencia) | checklist AGENTS.md flujo paso 7 |
| 6.2 | Push de `migracion/vps-limpieza` y merge a `main` con aprobación del Owner; registrar `RELEASE_SHA` en LOG.md | remotes actualizados |
| 6.3 | Destino del remote: bare repo en el VPS (`/opt/git/riotqueens.git`) como origen canónico; GitHub privado queda como opción futura del Owner | `git remote -v` |

---

## Fuera de alcance de esta migración (no abrir sin Owner)

- Nuevas features de producto, roster o asociaciones Queen↔Tier.
- Cambios a contratos, límites o arquitectura (requieren ADR propio).
- Gasto en GPU por encima del tope definido en Corte 4.
- Cualquier referencia a identidades históricas o material recuperado del trash.
