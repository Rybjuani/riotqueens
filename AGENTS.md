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
| **T0 free preview** | Bardera con `sao10k/l3.3-euryale-70b` vía OpenRouter | Activo; gratis/barato; límite diario |
| **T1** | Propiedades definidas; **nombre de modelo no inventar** | Primer escalón de experiencia conversacional inmersiva; solo si Owner nombra el modelo |
| **T2** | Propiedades definidas; **nombre de modelo no inventar** | Mejor modelo/calidad/memoria y compartición contextual de assets autorizados (foto/video); solo si Owner nombra el modelo |
| **T3 aspiracional** | `orcarouter/Qwen3.8-27B-Uncensored-FP8` en Vast.ai RTX 4090 spot | GPU **gated por Owner** |

- Los tiers escalan la experiencia de chat conversacional (modelo, calidad, memoria y assets autorizados); no crean una personalidad, profesión o capacidad semántica distinta para la Riot.
- `rg -i gemini` debe quedar vacío en configs y runtime. Gemini descartado.
- No nombrar el modelo técnico al usuario final; lenguaje humanizado.
- **`max_tokens`:** decisión técnico/comercial **independiente** de ROOT-like. Valor actual del runtime: **mantener** hasta nueva decisión explícita del Owner (no derivar de “80 líneas” ni de dogma de preset).

### 3.1 Datos de modelos y GPU (Owner, 2026-08-26)

Se priorizan modelos unrestricted con multimodalidad nativa o fine-tunes sin moralina corporativa, aptos para vLLM en FP8/GGUF. La abliteration de Qwen conserva el tower de visión; unrestricted y multimodalidad no son objetivos excluyentes.

| Repositorio / modelo | Método | Tracción / VRAM | Observación operacional |
|---|---|---|---|
| `orcarouter/Qwen3.8-27B-Uncensored-FP8` | Abliteration quirúrgica | ~29 GB FP8 | Seleccionado para T3; visión nativa; requiere GPU suficiente o cuantización adecuada |
| `cognitivecomputations/dolphin-3.0-mistral-24b` | Fine-tune completo | ~16–20 GB en 4/8-bit | Candidato: function calling y seguimiento de instrucciones robusto |
| `huihui-ai/Huihui-Qwen3.6-14B-Vision-abliterated` | Abliteration parcial | ~10–12 GB en 4-bit | Candidato: opción de GPU menor (p. ej. RTX 3090) con visión |
| `AEON-7/Qwen3.8-27B-AEON-ULTIMATE-UNCENSORED-BF16` | Abliteration por coherencia | ~29 GB BF16 | Candidato: evaluado sobre sets harmful/sexual/harmless |

Los tres marcados como **candidato** no son una asignación a T1/T2 ni autorización para inventar esa asignación. Solo el Owner puede seleccionar el modelo y proveedor de cada tier.

Referencia de capacidad spot (a validar contra la cuantización/contexto elegidos antes de gastar):

| Setup | Cuantización | VRAM de pesos | Costo orientativo |
|---|---|---|---|
| 1× RTX 4090 (24 GB) | FP8 o AWQ 4-bit | ~17–29 GB + KV cache | US$ 0.35–0.45/h |
| 1× RTX 3090 (24 GB) | GGUF Q4_K_M o FP8 | ~16–20 GB + KV cache | US$ 0.25–0.35/h |

### 3.2 vLLM, contexto y jurisdicción PAYG

- Para el pod self-hosted se usa vLLM directo, sin wrapper pesado. Base de referencia para el modelo que autorice el Owner:

  ```bash
  python3 -m vllm.entrypoints.openai.api_server \
    --model <MODELO_APROBADO> \
    --port 8000 \
    --api-key "$VLLM_API_KEY" \
    --enable-prefix-caching \
    --gpu-memory-utilization 0.90
  ```

- `--enable-prefix-caching` es obligatorio: el Dossier Maestro pesado es un system prompt repetido y no debe recomputarse íntegramente por turno.
- El chat puede transitar una instancia spot fuera de Canadá durante el procesamiento. La instancia no persiste conversaciones: el estado durable sigue en VPS/Postgres. La jurisdicción del proveedor concreto se revisa antes de contratarlo.
- La aceptación de voz se hace con hilo real manual del Owner y batería de modismos como regresión; queda derogada una matriz rígida 12/12 y no se paga contexto completo sólo para evaluar.
- Multimodalidad futura del modelo **no** equivale a feature pública: no se anuncia ni entrega hasta que la ruta esté implementada y validada.

### 3.3 Producto +18 y media

- `+18` es elegibilidad legal; el producto no es entretenimiento sexual explícito. Es chat adulto, rol conversacional y registro punk/conurbano.
- Los tiers agregan beneficios técnicos (adjuntar imagen, selfies con ropa, continuidad y recursos), no una personalidad, profesión o capacidad semántica distinta.
- No se entrega contenido sin ropa en ningún tier. Toda media premium requiere autorización server-owned antes de llegar al navegador.
- La conversación no se cape a por palabras sexuales, vulgares o técnicas: el límite de media es una capacidad real del producto, no un keyword filter.

### 3.4 Transición cloud y memoria

- El T0 cloud actual es un puente, no el estado final de voz. Si un provider externo produce refusals incompatibles o rompe coherencia/memoria, no se parchea el adaptador ni se deforma a Bardera: se migra a ejecución unrestricted self-hosted cuando el Owner habilite la infraestructura.
- P1 (Owner Investigation, 2026-08-29) desbloquea la preparación fullstack de T1/T2/T3. La contratación y el gasto de la instancia Vast.ai RTX 4090 spot siguen siendo acción exclusiva del Owner; el cutover T3 queda para el final.

---

## 4. Topología documental final

1. `/AGENTS.md` — este archivo.
2. `/DOSSIER_MAESTRO.md` — único dossier (núcleo Riot + Bardera + relación + mirroring + cultura + intensidad + afecto + sensualidad con código + continuidad + vocabulario/cooldowns + anti-patrones + evals + casting).
3. `/README.md` — mapa técnico no autoritativo.
4. `/_trash_scratch/` — forense, sin autoridad.
5. `prompts/bardera.preset.md` — **forense / no autoritativo** para reconstrucción; runtime carga el Dossier Maestro completo.
6. `/Riotqueens-Ai-Landing-Mock.html` — referencia visual canónica versionada. Guía el ADN de la readaptación (negro, magenta, cyan, display punk/editorial, labels técnicos, energía y slogans); no se copia literalmente ni sustituye las decisiones activas de tiers, precios, capacidad o copy.

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
| 7 | P1 — Owner Investigation | **Cerrado / decidido (2026-08-29):** preparar estructura fullstack T1/T2/T3; T3 = `orcarouter/Qwen3.8-27B-Uncensored-FP8`; provider final = Vast.ai RTX 4090 spot contratada por Owner |
| 8 | Identidad visual | **`Riotqueens-Ai-Landing-Mock.html` manda como ADN visual.** Readaptar la web actual sin romper su estructura útil; conservar slogans, sumar los faltantes y mantener coherencia de léxico, modismos, manifiestos, colores y estilo |
| 9 | Owner Console visual | **Aprobada (2026-08-29):** consola de chat continuo para diagnóstico en UI privada. Se sirve sólo por `127.0.0.1` del VPS y túnel SSH; Root conserva el cartel upstream crudo. El bearer de Auth0 se carga una vez por sesión de pestaña y no se persiste en Git, runtime ni `localStorage`. |
| 10 | Prueba T0 context-fit | **Aprobada temporalmente (2026-08-29):** para validar T0 bajo el límite upstream gratuito, el runtime usa un único Dossier Maestro compacto con margen para el hilo. El Dossier pleno previo está preservado por el tag `dossier-full-pre-t0-compact-20260829` y el release `ca3da33`; se restaura si el Owner rechaza el test. No es una decisión final de personalidad ni de provider. |

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
- La UI de Owner Console también queda fuera de Caddy público: se abre por el puerto web loopback tunelizado junto con el API. El token se conserva, como máximo, en `sessionStorage` de esa pestaña; jamás se registra en logs ni se envía al chat público.

---

## 7. Workflow para agentes

1. Leer este `AGENTS.md`.
2. Si la tarea toca personalidad/casting/evals → leer `/DOSSIER_MAESTRO.md`.
3. Si hay opciones de diseño → **REPORT OPTIONS** y esperar. No ejecutar arquitectura no autorizada.
4. Push a `origin` solo con pedido explícito del Owner.
5. Deploy a VPS solo con pedido explícito, vía procedimiento §8.
6. Si duda: no inventar; escalar al Owner.

### 7.1 Alcance autorizado por P1

- Codex puede preparar ahora los contratos y la estructura fullstack para T1/T2/T3: resolución de tier server-owned, configuración de provider/modelo sin secretos, ventanas de contexto/memoria por tier y entrega de assets autorizados por backend.
- No hardcodear ni activar un modelo T1/T2 hasta que el Owner lo nombre. No contratar, encender ni facturar GPU: Vast.ai RTX 4090 spot la contrata el Owner cuando corresponda.
- La readaptación visual parte del mock canónico. Se preserva la arquitectura funcional existente (auth, consentimiento, chat, continuidad y superficies privadas), y se pule su presentación y copy sin degradar esas funciones.

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
