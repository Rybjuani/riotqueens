# RiotQueens.ai

RiotQueens.ai es una experiencia `+18` de personajes virtuales ficticios, originales y curados por el owner. La plataforma pone a cada Queen al frente y esconde la complejidad de modelos, memoria, proveedores y media detrás de una conversación coherente.

> **LANDINGS MANDAN. PRODUCTO DEBAJO. COMPLEJIDAD ESCONDIDA. QUEEN AL FRENTE.**

## Canon

- [`SPECT.md`](SPECT.md): producto, arquitectura, estado verificado y próximos cortes.
- [`AGENTS.md`](AGENTS.md): reglas operativas para cualquier agente o contribuidor.
- [`RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md`](RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md): checkpoint operativo vigente y continuidad para el siguiente agente.
- [`docs/DECISION_REGISTER.md`](docs/DECISION_REGISTER.md): decisiones recuperadas, estado y pendientes que no deben volver a depender de un chat.
- [`docs/EXTERNAL_FAILURE_PATTERN.md`](docs/EXTERNAL_FAILURE_PATTERN.md): patrón sanitizado de ruptura de scope, contexto y personaje observado en productos externos.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): contrato y evidencia del primer despliegue.
- `docs/reference/visual/Riotqueens-Ai-Landing-Mock.html`: autoridad visual, compositiva y de ADN de diseño dentro del alcance reconocido por las fuentes vigentes.
- `docs/reference/visual/Reiniciando-chat-anterior.html`: autoridad de continuidad e interacción.

`RiotQueens-worktree` es el único repo canónico porque contiene Git, CI,
despliegue, código, documentación y el patrimonio creativo operativo. Los
masters seleccionados viven en `assets/private/selected/` (gitignored); los
derivados públicos viven en `apps/web/public/`. No existe un segundo árbol
necesario para ejecutar, entender o desplegar RiotQueens.

La documentación stale se elimina del HEAD y su respaldo de contingencia se guarda en `/home/rybjuani/Documentos/_scratch_trash/`; sólo puede recuperarse por decisión explícita actual del owner.

Las copias crudas de los landings están registradas por SHA-256 en el SPECT y permanecen fuera del runtime por sus bundles y datos embebidos. Su composición y su flujo ya fueron auditados y portados al frontend funcional. El logo oficial y los assets provisionales versionados conservan procedencia y hash en [`docs/ASSET_PROVENANCE.md`](docs/ASSET_PROVENANCE.md).

## Estado real

### Implementado

- monorepo `pnpm`;
- frontend Next.js alineado con los dos landings canon;
- backend FastAPI;
- router desacoplado y proveedor OpenAI-compatible;
- mock para desarrollo y pruebas;
- prompt de sistema controlado por servidor;
- salida LLM validada, fallback secundario opcional y continuidad server-owned;
- La Bardera como Queen canónica y única implementada en runtime;
- experiencia activa T0/free con Bardera, independiente de los tiers T1–T3 todavía no definidos;
- Queen registrada, routing y contexto validados del lado servidor; `/v1/chat` no acepta una ruta elegida por el cliente ni expone diagnósticos internos del provider;
- conversación multi-turn y memorias explícitas **durables en PostgreSQL** cuando
  hay `DATABASE_URL` (migraciones `0002`); fallback in-process solo sin DB/tests;
- clickwrap +18 versionado (ADR 0004): UI + `/v1/consent/*` + tabla append-only
  `0003`; gate de chat con auth habilitada;
- C3 de identidad no productivo: Auth0 CA sólo como IAM, binding transaccional
  `sub` → UUID RiotQueens propio, JWT fail-closed y browser ID sin autoridad;
- tenant Auth0 CA + Custom API audience configurados en `.env` local; preprod HTTP
  por IP sigue con auth desactivada hasta callbacks de Application + dominio;
- retries, errores tipados, validación y tests;
- flujo landing → chat, tiers, páginas legal/privacidad y responsive verificados localmente;
- Caddy como entrada única para web y `/api/*`;
- allowlist SHA-256 que impide incorporar media premium o no registrada a `public/`;
- preprod HTTP por IP en `148.113.167.121` con release `7448898`;
- casting de voz Bardera cerrado: primario Gemini 3.1 Flash Lite, fallback lab
  Euryale 70B (OpenRouter); no reabrir Dolphin ni matriz de casting;
- al deploy de `7448898` el VPS aún reportaba `mode=mock` hasta activar el
  runtime real en `runtime.env`.

### Todavía no implementado

- clickwrap +18 versionado y validado por backend;
- Auth0 para usuarios de prueba en preprod/producción (Custom API, migración y
  secretos del VPS cuando se active el runtime protegido);
- persistencia durable de conversaciones y memorias;
- storage privado, CDN y URLs firmadas;
- entitlements, créditos y pagos;
- entrega autorizada de media premium;
- Cloud Lab conectado al producto (dirección futura documentada; no disponible);
- dominio de producción y TLS validados.

Un reinicio de la API borra conversación y memoria actuales. Los identificadores de usuario prototipo y conversación son scopes controlados por el navegador, no cuentas ni identidades seguras. La API rechaza Queens no registradas y ya no publica endpoints WIP de perfil, personajes configurables o media mock.

## Stack

- Next.js 14, React 18 y TypeScript
- FastAPI, Python 3.12, Pydantic y HTTPX
- PostgreSQL y Redis como objetivos de infraestructura
- Docker Compose para ejecución y despliegue
- proveedor de modelos desacoplado mediante adaptadores

## Cómo se construye una Queen

La esencia compartida de RiotQueens se combina con una identidad, voz, glosario y benchmark independientes por Queen. [`docs/QUEEN_CURATION_PIPELINE.md`](docs/QUEEN_CURATION_PIPELINE.md) documenta el flujo NotebookLM → informe estructurado → perfil versionado → prueba de modelo → registro de aprobación. Aprobar el benchmark de modismos de La Bardera es un criterio de casting para ese modelo y esa configuración; no convierte a Bardera en la voz de las demás.

`Qwen_html.html`, `MANIFIESTO_BARDI.pdf`, `barderainvernadero.png` y los manifiestos del owner fueron auditados como fuentes de diseño, misión, visión y curaduría. El snapshot de `Qwen_html.html` está en [`docs/reference/audits/`](docs/reference/audits/); los demás originales privados siguen fuera del repo. Ninguno se copia automáticamente al runtime: su clasificación y hashes están en [`docs/canon/QUEEN_SOURCE_REGISTER.md`](docs/canon/QUEEN_SOURCE_REGISTER.md).

## Mapa único de trabajo

Para evitar otra bola de nieve, cada tipo de decisión tiene una sola ubicación:

| Necesidad | Fuente vigente |
|---|---|
| producto, arquitectura, canon funcional y capacidades publicables | [`SPECT.md`](SPECT.md) |
| continuidad operativa y próximos cortes | [`RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md`](RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md) |
| decisiones, contradicciones y pendientes | [`docs/DECISION_REGISTER.md`](docs/DECISION_REGISTER.md) y ADRs |
| procedencia de fuentes y assets | [`docs/canon/QUEEN_SOURCE_REGISTER.md`](docs/canon/QUEEN_SOURCE_REGISTER.md) y [`docs/ASSET_PROVENANCE.md`](docs/ASSET_PROVENANCE.md) |
| perfiles, glosarios y casting por Queen | [`docs/QUEEN_CURATION_PIPELINE.md`](docs/QUEEN_CURATION_PIPELINE.md) y `docs/canon/queens/` |
| modelos, benchmarks y credenciales de laboratorio | [`docs/PROVIDER_LAB.md`](docs/PROVIDER_LAB.md) y `docs/evals/` |
| despliegue y estado del VPS | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |

Una transcripción externa, export de otro agente o documento histórico sólo se incorpora después de clasificarlo en una de esas fuentes; no crea una autoridad paralela. Los catálogos externos de Flow/Mage no son autoridad hasta que una selección concreta se registra con procedencia y hash.

## Proveedores y laboratorio

**Primario de producto (casting cerrado 2026-08-17):** Google AI Studio OpenAI-compatible + `gemini-3.1-flash-lite`.  
**Fallback de lab:** OpenRouter + `sao10k/l3.3-euryale-70b` (Euryale 70B).  
No reabrir casting ni promover Dolphin Venice (falla de identidad/dossier). Preprod en
`148.113.167.121` corre `mode=real` con ese par. Multimodalidad y self-host
(Gemma/Ollama) siguen en [`docs/PROVIDER_LAB.md`](docs/PROVIDER_LAB.md) sin promesa pública.

## Repositorio

```text
apps/web/       frontend actual
apps/api/       API, dominio, proveedores y tests
ops/            proxy y contrato operativo
config/         políticas verificables, incluida la allowlist de media pública
SPECT.md        especificación canónica vigente
AGENTS.md       reglas de contribución y orquestación
```

## Desarrollo local

Requisitos: Python 3.12+, Node 20+, pnpm 9+ y Docker Compose.

```bash
cp .env.example .env
make setup
make lint
make test
```

El Compose de lanzamiento ejecuta `postgres`, `web`, `api` y `caddy`. Redis sigue
opcional. El proveedor por defecto en `.env.example` es `mock`; preprod usa Gemini real.

Variables server-side en `.env.example` (`RIOTQUEENS_MODEL_*`, fallback, lab keys).
Ninguna clave se expone al frontend. El único archivo de configuración local es
`.env` en la raíz de este repo, ignorado por Git.

## Próximo objetivo

1. **Registrar** el dominio `riotqueens.ai` (hoy no registrado) y `A` → `148.113.167.121`;
2. TLS con Caddy (`SITE_ADDRESS=riotqueens.ai`) y smoke HTTPS;
3. Auth0 Application callbacks para IP/dominio + flip `RIOTQUEENS_AUTH_ENABLED` /
   `NEXT_PUBLIC_AUTH_ENABLED` en VPS + smoke login → clickwrap → chat;
4. cerrar jurisdicciones, textos legales reforzados y retención antes de producción;
5. media privada y entitlements sólo después de autorización y oferta comercial.

Para retomar el trabajo, leer en este orden: `AGENTS.md`, `SPECT.md`, este README, el handoff operativo, `docs/DECISION_REGISTER.md` y el documento específico de la tarea. Cada cambio debe dejar evidencia, pruebas proporcionales y un commit convencional.
