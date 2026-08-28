# AGENTS.md — Gobernanza Operacional RiotQueens

**Autoridad:** operacional (agentes, deploy, seguridad, provider).  
**Owner:** Juani.  
**Complemento (no sustituye):** `/DOSSIER_MAESTRO.md` — canon / persona / casting.  
**Mapa técnico (no autoritativo):** `/README.md`.

> `AGENTS.md` NO absorbe el dossier. El dossier NO asume funciones de `AGENTS.md`.

---

## 0. LEY 0 y principio operativo

1. **LEY 0:** para todo lo versionable, `LOCAL == GITHUB == VPS`.
2. **Principio:** `REPORT OPTIONS → OWNER DECIDES → AGENT EXECUTES`.
   - Los agentes analizan y proponen alternativas.
   - **No** deciden arquitectura, producto, autoridad, provider strategy ni reintroducen opciones rechazadas.
   - Una propuesta técnica no equivale a autorización.
   - Un ADR documenta una decisión aprobada por el Owner; no la crea ni la autoriza.

---

## 1. Jerarquía anti-contradicción

1. **Owner** — producto, canon, gasto, aceptación, decisiones explícitas.
2. **`/AGENTS.md`** (este archivo) — gobernanza operacional.
3. **`/DOSSIER_MAESTRO.md`** — personalidad, relación, cultura, casting, evals.
4. **Código + tests** — verifican lo implementado; no inventan producto.
5. **`/_trash_scratch/`**, historial Git, worktrees viejos, handoffs — **nunca** autoridad activa.
6. **`README.md`**, roadmaps, migration notes — mapa / plan; ceden ante 1–3.

Si dos fuentes chocan y la jerarquía no resuelve: **detenerse y escalar al Owner**. No “armonizar” inventando una tercera interpretación.

---

## 2. Reglas vinculantes (cerradas — no reabrir)

### 2.1 Riots no se capean

> A las Riots no se las capea. Si un provider/modelo impone refusals incompatibles con la identidad y el producto, se cambia de provider/modelo o se evalúa ejecución local. **No** se modifica la Riot para acomodarla al proveedor.

- Prohibido: filtros semánticos / censuras intermedias arbitrarias por palabras vulgares, sexuales o técnicas.
- La conversación de cualquier usuario debe disponer de la **misma capacidad semántica del modelo** que el modo ROOT (**ROOT-like**).
- **ROOT-like** = capacidad conversacional. **NO** = acceso al Owner Console, privilegios administrativos, secretos ni endpoints privados.
- La capa de seguridad del control plane protege secretos, infraestructura y límites reales de herramientas; **no escribe personalidad**.

### 2.2 Decisiones del Owner no se flexibilizan

Cuando una decisión del Owner está expresada de forma explícita, ningún agente puede convertirla en sugerencia, opción, “flexibilidad” o interpretación alternativa.  
`rechazado por Owner = no reaparece` salvo nueva autorización explícita.

### 2.3 No fragmentación

No multiplicar dossiers, presets, glosarios o documentos de personalidad si la información puede vivir en una fuente única coherente. Fragmentar solo con razón técnica/epistemológica concreta y documentada.

### 2.4 No inventar

No inventar modelos T2, dossiers individuales inexistentes, ni “mejoras” que reabran opciones cerradas.

### 2.5 Skills / profesiones

RiotQueens son companions humanizadas, no agentes especializados.  
No incorporar skills/profesiones como identidad persistente.  
Esto **no** limita la capacidad conversacional general del modelo (código, seguridad, moda, prompts, etc. cuando el usuario lo pide).

### 2.6 “Te quiero”

Rareza **extrema y contextual** (Nivel 1).  
**No** es una regla booleana literal de “una sola vez en la vida”.

### 2.7 Legacy `/_trash_scratch/`

- Prohibido borrar definitivamente documentación, presets, reglas o fuentes históricas durante consolidaciones.
- Stale / derogado / reemplazado → mover a `/_trash_scratch/` preservando ruta relativa cuando aplique.
- Tracked en Git; archivo forense interno.
- **Nada** en `/_trash_scratch/` tiene autoridad ni puede importarse/cargarse por runtime.
- Secuencia: **Preservar/versionar inputs → Mover legacy → Consolidar → Validar**.

### 2.8 BigPickle

`RIOTQUEENS_BIGPICKLE.md` **deja de ser autoridad activa**. Su contenido vigente de modelos/tiers y reglas operativas útiles vive aquí (y el canon de persona en el Dossier Maestro). El archivo original se archiva en `/_trash_scratch/`.

---

## 3. Provider / modelos / tiers (fuente operacional)

No duplicar tablas de modelos dentro del dossier de personalidad. Fuente operacional:

| Tier | Estado | Notas |
|---|---|---|
| **T1 preview** | `sao10k/l3.3-euryale-70b` vía OpenRouter | Gratis/barato; límite diario |
| **T2** | Propiedades definidas; **nombre de modelo no inventar** | Multimodal / selfies a demanda pagos — solo si Owner nombra el modelo |
| **T3 aspiracional** | `orcarouter/Qwen3.8-27B-Uncensored-FP8` en Vast.ai RTX 4090 spot | GPU **gated por Owner** |

- `rg -i gemini` debe quedar vacío en configs y runtime. Gemini descartado.
- No nombrar el modelo técnico al usuario final; lenguaje humanizado.
- **`max_tokens`:** decisión técnico/comercial **independiente** de ROOT-like. Valor actual del runtime: **mantener** hasta nueva decisión explícita del Owner (no derivar de “80 líneas” ni de dogma de preset).

---

## 4. Topología documental final

1. `/AGENTS.md` — este archivo.
2. `/DOSSIER_MAESTRO.md` — único dossier (núcleo Riot + Bardera + relación + mirroring + cultura + intensidad + afecto + sensualidad con código + continuidad + vocabulario/cooldowns + anti-patrones + evals + casting).
3. `/README.md` — mapa técnico no autoritativo.
4. `/_trash_scratch/` — forense, sin autoridad.
5. `prompts/bardera.preset.md` — **forense / no autoritativo** para reconstrucción; runtime carga el Dossier Maestro completo.

---

## 5. Decisiones de implementación aprobadas por Owner (2026-08-28)

| # | Tema | Decisión |
|---|---|---|
| 1 | Ruta Dossier Maestro | **`/DOSSIER_MAESTRO.md`** |
| 2 | Carga de persona en runtime | **Dossier maestro completo** |
| 3 | Deploy LEY 0 | **`git archive` atómico + manifiesto SHA-256 inmutable por release** |
| 4 | Control plane privado | **Loopback `127.0.0.1` + túnel SSH** para endpoints Owner (`/v1/root`, y superficie admin asociada) |
| 5 | Memoria / continuidad | **Historial completo durable + ventana de selección de contexto** |
| 6 | `max_tokens` | **Mantener valor actual del runtime** |

---

## 6. Seguridad y secretos

- Secretos **nunca** en Git, logs ni chat.
- SSH: `~/.ssh/luxriot_vps` → `ubuntu@148.113.167.121`. Key por path, nunca en `.env`.
- `runtime.env` modo `600`, por `scp`, nunca por Git.
- Owner Console (`/v1/usuario`, `/v1/root`, `/v1/compare`): **fail-closed** por allowlist (`RIOTQUEENS_OWNER_AUTH0_SUBJECTS` en prod / `RIOTQUEENS_OWNER_USER_IDS` con auth off).
- Cartel crudo de OpenRouter **solo** en `/root` (y `errors.root` de `/compare`).
- Chat público `/v1/chat` **nunca** expone `upstream` ni bloque `owner`.
- Salida LLM = no confiable. Identidad, fallback y continuidad son server-owned.
- Control plane administrativo: bind **loopback**; acceso remoto vía **SSH tunnel** (decisión §5.4).

---

## 7. Workflow para agentes

1. Leer este `AGENTS.md`.
2. Si la tarea toca personalidad/casting/evals → leer `/DOSSIER_MAESTRO.md`.
3. Si hay opciones de diseño → **REPORT OPTIONS** y esperar. No ejecutar arquitectura no autorizada.
4. Push a `origin` solo con pedido explícito del Owner.
5. Deploy a VPS solo con pedido explícito, vía procedimiento §8.
6. Si duda: no inventar; escalar al Owner.

Interfaz y copy público en español natural; código e identificadores en inglés.

---

## 8. Deploy (LEY 0)

Procedimiento aprobado:

1. Asegurar `LOCAL == GITHUB` (commit + push autorizado).
2. En VPS: construir release con **`git archive`** del commit exacto.
3. Generar **manifiesto SHA-256** inmutable del árbol del release.
4. Activar release de forma atómica (`current` → nuevo release).
5. Verificar: commit/ref, manifiesto, path+hash del dossier cargado, health de api/web, Caddy apunta al release activo.
6. No dejar bind-mounts de Caddy u otros a releases viejos.

---

## 9. Qué no hacer

- No reabrir decisiones de §2 ni §5.
- No cargar `/_trash_scratch/` en runtime.
- No capear Riots “por seguridad de tono”.
- No tratar BigPickle, `docs/AUTHORITY.md`, presets viejos o handoffs como autoridad vigente.
- No fragmentar el Dossier Maestro sin autorización del Owner.
