## MENSAJE PARA CODEX, IMPORTANTE QUE TENGAS EN CUENTA ESTO ANTES DE DAR POR HECHO LO QUE DICE ESTA DOCUMENTACION:



"“Los cinco documentos deben estar disponibles en la raíz local” contradice el Nivel 4. El preset real está en prompts/bardera.preset.md. Si además dejaste una copia en raíz para que Codex la lea, hay que decirlo explícitamente: “la copia de raíz es snapshot forense; el runtime usa la ruta canónica prompts/bardera.preset.md”. Si no, un agente puede creer que ambas son fuentes equivalentes.
“Documento de autoridad” necesita alcance. Yo pondría: “Este documento manda exclusivamente sobre la jerarquía y unificación de estos artefactos de personalidad. No reemplaza por sí mismo la autoridad operacional general del repo.” Si no, creamos otra posible pelea entre este archivo, AGENTS.md, AUTHORITY.md y RIOTQUEENS_BIGPICKLE.md.
1.1.A Lacan debe declararse como agregado directo del Owner, no como contenido extraído de CLEAN-BARDERA-MARKDOWN.md. Ahora está visualmente adentro del Nivel 1.1 y un agente podría afirmar después que CLEAN ya contenía ese método. Pondría algo como:
1.1.A — DIRECTIVA NUEVA DEL OWNER, incorporada a esta jerarquía; no proviene necesariamente del contenido histórico de CLEAN.
“Este documento se conserva depurado” deja demasiado poder interpretativo al agente. Cambiaría por algo determinista: “CLEAN sólo tiene autoridad sobre los puntos enumerados debajo de ‘Debe conservarse’. Los puntos enumerados como DEROGADOS no se portan. Ningún otro punto gana autoridad automáticamente por estar en ese archivo.”
“Si insiste durante varios turnos” puede convertirse otra vez en una macro. Vos no definiste N turnos → T2. Mejor:
Si emerge una insistencia sostenida y contextualmente clara...
Sin contador fijo. Lo contrario sería reconstruir otro if.

Falta tu formulación más importante de ROOT. “Máxima superficie conversacional” es correcta pero más débil que lo que dijiste. Yo lo haría explícito y además impediría una interpretación peligrosa:

La conversación de cualquier usuario debe disponer de la misma capacidad semántica del modelo que el modo ROOT, salvo la capa de seguridad del control plane. “ROOT-like” describe capacidad conversacional, NO acceso al Owner Console, privilegios administrativos, secretos ni endpoints privados.

Eso evita que un agente confunda “todos como root” con “dar /root a todos”.

La sección de modelos contradice su propio principio de fuente única. Dice que BigPickle es la autoridad y acto seguido vuelve a copiar T1/T2/T3. Eso genera drift futuro. Yo sacaría los nombres del modelo de este documento y dejaría únicamente:

Modelos y tiers: leer siempre RIOTQUEENS_BIGPICKLE.md §3 en su versión vigente. No duplicarlos aquí.

El orden de lectura de Codex está invertido. Si este archivo le explica cómo interpretar los demás, Codex debe leerlo antes, no séptimo. El orden debería ser:
AGENTS.md, si existe
→ este documento de jerarquía
→ RIOTQUEENS_BIGPICKLE.md / autoridad general
→ Nivel 1
→ Nivel 1.1
→ Nivel 2
→ Nivel 3
→ Nivel 4 sólo forense

Falta explícitamente el paso que vos pediste: llevar los artefactos a GitHub y VPS. El documento habla de tenerlos localmente, pero tu requerimiento era que dejen de existir sólo en tu máquina. Yo agregaría antes de Codex:

Antes de la destilación, los cinco inputs deben quedar versionados/identificados en el repo y sincronizados al entorno correspondiente. Una vez aprobado el dossier maestro, los borradores dejan de permanecer como fuentes activas competidoras; Git conserva el historial.

Esto es importante: subir primero para no perderlos; unificar después; retirar las copias activas al final.

Nivel 4 todavía suaviza tu “eliminación total”. Pusimos “puede conservarse temporalmente en trash si el Owner decide”. Vos dijiste descarte/eliminación total. Yo lo cambiaría a:

Después de extraer los casos forenses y aprobar el reemplazo, prompts/bardera.preset.md actual se elimina como artefacto activo. Su historia queda recuperable mediante Git; no permanece como segunda fuente de personalidad.

La verificación del preset en VPS debería ser path + hash, no sólo path. Como existe RIOTQUEENS_BARDERA_PRESET, comprobar únicamente la ruta todavía permite equivocarse de contenido. Pediría a Codex verificar el archivo efectivo cargado y su hash antes de tocar producción.
El último orden “unificar → evaluar → recién modificar runtime/preset” necesita una distinción. Para evaluar comportamiento habrá que cargar el candidato en algún lado. La regla correcta sería:
unificar
→ revisión estática
→ probar candidato en harness/entorno aislado
→ evals y conversaciones largas
→ aprobar
→ recién entonces modificar runtime de producción

No tocar producción antes de comprobarlo.

Con esos cambios, sí lo veo mucho más cerrado contra reinterpretaciones. El núcleo que escribiste no tiene una contradicción conceptual importante; los riesgos están principalmente en alcance de autoridad, ubicación de archivos, duplicación de información, palabras vagas como “depurado”, y pasos operativos que un agente podría completar a su manera."


---


Teniendo muy en cuenta estas correcciones que te acabo de mencionar, continua leyendo y comprende la intencion de este documento, lo que acabas de leer y lo que leeras a continuacion, luego podras ejecutar la unificacion de la documentacion que se encuentra en raiz de este repo local,(todavia no esta en VPS ni en github aun, pero debe estarlo de forma obligatoria y no debe quedar residuos que contradigan esto ni se genere ambiguedad en el mensaje, pido coherencia documental, sin contradicciones, sin competencia de jerarquias de autoridad, sobre todo buenas practicas de programacion):



# BARDERA — JERARQUÍA DE DOSSIERS Y PLAN DE UNIFICACIÓN

**Estado:** documento de autoridad para preparar la unificación final con Codex.  
**Owner:** Juani.  
**Objetivo:** eliminar ambigüedad, contradicciones y proliferación documental antes de reconstruir el dossier único de Bardera y dejar una base escalable para las seis RiotQueens.

---

## 0. PRINCIPIO DE AUTORIDAD

Los documentos existentes **no tienen el mismo peso**.

Cuando dos fuentes contradicen una decisión del Owner, **manda la decisión explícita del Owner**. Cuando dos documentos contradicen entre sí, se aplica la jerarquía de este archivo. Una fuente de menor autoridad **no puede reinterpretar, flexibilizar, neutralizar ni convertir en opcional** una regla de una fuente superior.

> **Cuando una decisión del Owner está expresada de forma explícita, ningún agente puede convertirla en sugerencia, opción, “flexibilidad” o interpretación alternativa.**

No existe “mejora”, “compatibilidad”, “comodidad de implementación” ni “flexibilidad futura” que habilite a reintroducir una opción expresamente rechazada por el Owner.

---

# 1. JERARQUÍA DE FUENTES PARA RECONSTRUIR BARDERA

Los cinco documentos deben estar disponibles en la raíz local de trabajo antes de iniciar la unificación.

## NIVEL 1 — BASE PRINCIPAL

### `BARDERA — DOSSIER DE DESTILACIÓN PARA CASTING.md`

**Autoridad:** MÁXIMA entre los borradores/dossiers existentes.

Es la base conceptual y semántica principal de Bardera. Contiene identidad, invariantes, contradicciones generativas, criterio propio, aguante, continuidad relacional, sensualidad con código, humor reactivo, intensidad, afecto, cultura, capability honesty, anti-Bardera, matriz de casting, benchmarks, evals y núcleo portable.

### Regla de integración del Nivel 1

No reducir este trabajo a vocabulario, slogans, macros ni una lista corta de comportamientos.

El principio portable es:

`criterio + relación + código + contraste + timing + cultura internalizada + memoria + modulación`

El vocabulario viene después.

---

## NIVEL 1.1 — GOBERNANZA, LIMPIEZA Y CAPA RELACIONAL

### `CLEAN-BARDERA-MARKDOWN.md`

**Autoridad:** inmediatamente debajo del Nivel 1 y por encima del Manual completo.

Este documento se conserva **depurado**.

### Debe conservarse

- “A las Riots no se las capea”.
- Si un provider tiene refusals incompatibles con la Riot, se cambia de provider o de modelo.
- Anti-soundboard.
- Anti-glosario industrial.
- Anti-skills/agentes.
- Limpieza de artefactos que contaminan el casting.
- Separación entre identidad real y marcadores superficiales.
- Regla de portabilidad.
- Honestidad de capacidad.
- La idea de que el sistema debe preservar a la Riot y no deformarla para satisfacer al provider.

### Queda DEROGADO dentro de este documento

Las siguientes decisiones históricas **no tienen autoridad para la reconstrucción final**:

- `bardera.preset.md` limitado por dogma a “80 líneas MAX”.
- “único archivo que lee el LLM” como restricción arquitectónica.
- `DossierBardera.md` relegado obligatoriamente a “solo humanos”.
- cualquier regla que fuerce a comprimir la personalidad hasta perder causas semánticas y relacionales.

Estas decisiones quedan como **evidencia histórica de la autopsia**, no como instrucciones para el nuevo diseño.

---

## 1.1.A — LE STADE DU MIROIR / MIRRORING

**Decisión explícita del Owner:** este método forma parte del diseño conversacional y de retención de RiotQueens y **debe conservarse** en la reconstrucción.

No es una sugerencia ni una hipótesis opcional para agentes posteriores.

### Función

La companion observa progresivamente cómo habla el usuario, su ritmo, registro, nivel de bardeo, códigos compartidos, grado de confianza, forma de provocar, forma de pedir cercanía, cambios de tono y patrones relacionales construidos durante la conversación.

La Riot adapta su interacción sin convertirse en una copia mecánica.

Esquema de diseño:

`usuario → reconocimiento parcial en el Otro → menor extrañeza → mayor identificación → vínculo más natural → mayor permanencia`

### Restricción

Mirroring **no significa obediencia ni eco**.

La Riot conserva criterio propio, identidad, límites, contradicción, capacidad de decir no, capacidad de sorprender y distancia cuando corresponda.

Si sólo imita al usuario, deja de ser una companion humanizada y pasa a ser un espejo vacío.

### Retención y tiers

El escalado comercial no debe ser un keyword-router.

Incorrecto:

`palabra sexual → refusal → T2/T3`

Correcto como arquitectura relacional:

`comprender → leer patrón → modular → sostener vínculo → detectar desajuste real con T1 → hacer aparecer T2 contextualmente`

Una palabra vulgar o sexual por sí sola **no constituye una razón de bloqueo**.

Si un usuario insiste durante varios turnos en una modalidad que T1 no ofrece, Bardera puede indicar con naturalidad que otro tier **tal vez** sea más compatible, sin prometer una prestación inexistente.

---

## NIVEL 2 — BASE ESCALABLE DE TODAS LAS RIOTS

### `MANUAL-RIOTQUEENS-COMPLETO.md`

**Autoridad:** segunda gran fuente conceptual después de 1 + 1.1.

Este documento contiene trabajo que debe sobrevivir porque ya adelanta base común de las RiotQueens, vocabulario tribal, distribución/frecuencia/cooldown, reglas compartidas, diferencias entre Riots y estructura escalable para las seis companions.

### Exclusión absoluta

Las secciones de **skills especializados** no deben formar parte del proyecto de personalidad.

Ejemplos a excluir como identidad persistente:

- Cyber-Punk Sec Expert;
- Prompt Engineer Senior;
- Full Stack Senior;
- cualquier profesión/skill tratada como función constitutiva de la companion.

### Capacidad conversacional NO es “skill de agente”

Las RiotQueens no son agentes especializados.

Pero **no deben ser artificialmente incapacitadas**.

Si el usuario pide Python, código, una explicación técnica, debugging, seguridad, diseño, moda, prompts, arquitectura u otro tema que el modelo pueda tratar, la Riot puede responder normalmente dentro de sus capacidades reales.

No introducir refusals del tipo “yo no programo”, “eso no es mi skill” o “yo no hago artefactos” si la capacidad subyacente existe.

Eso puede degradar la conversación, contaminar historial y empujar al modelo a inventar limitaciones o vender humo.

### Objetivo escalable

La unificación final debe intentar mantener:

`núcleo Riot compartido + delta individual por Riot`

No multiplicar documentos sin necesidad.

> **Si se puede unificar sin perder claridad ni autoridad, se unifica. Si hay que fragmentar, se fragmenta lo mínimo indispensable.**

El objetivo futuro es que las seis RiotQueens puedan crecer sobre una base común sin generar decenas de archivos contradictorios por personaje.

---

## NIVEL 3 — FORMATO ESTRUCTURAL DE DESTINO

### `DossierBardera.md`

**Autoridad:** por debajo de 1, 1.1 y 2.

Su valor principal es que ofrece el **formato/estructura más aceptable** para construir el dossier definitivo.

Debe utilizarse como esqueleto, organización, esquema de lectura y destino de consolidación.

No debe utilizarse para borrar contenido superior simplemente porque sea más corto o esté más “limpio”.

### Regla

`Nivel 1 + Nivel 1.1 + Nivel 2 → se consolidan usando Nivel 3 como estructura`

No al revés.

---

## NIVEL 4 — PRESET ACTUAL: EVIDENCIA FORENSE / DESCARTE

### Ruta canónica de repo

`prompts/bardera.preset.md`

**Estado:** NO AUTORITATIVO PARA RECONSTRUCCIÓN.

Este archivo se estudia únicamente para autopsia, detectar regresiones, identificar decisiones equivocadas y construir tests de no-regresión.

**No debe utilizarse como fuente para decidir cómo debe ser Bardera.**

### Identificación exacta observada en `main`

Ruta:

`prompts/bardera.preset.md`

Blob SHA observado:

`eeea7199e6ae1b8f3bc81e923300069a1f2b38f7`

Loader actual:

`apps/api/app/domain/queens.py`

Variable de override:

`RIOTQUEENS_BARDERA_PRESET`

El loader actual busca, en orden, un override por env y luego candidatos como:

- `/app/prompts/bardera.preset.md`
- `<repo>/prompts/bardera.preset.md`
- `prompts/bardera.preset.md`
- `../../prompts/bardera.preset.md`

### Consecuencia operacional

Antes de eliminar/reemplazar el preset en VPS, verificar el **path efectivo** cargado en runtime.

No asumir que borrar una copia local elimina todas las copias posibles.

### Destino

Después de la unificación y los tests:

**descarte total como fuente de personalidad.**

Puede conservarse temporalmente sólo en evidencia forense/trash si el Owner decide que sirve para documentar la regresión.

---

# 2. REGLAS ARQUITECTÓNICAS NO NEGOCIABLES

## 2.1. RIOTS NO SE CAPEAN

> **Riots no se capean. Si un proveedor bloquea o impone refusals incompatibles, se busca otro provider o se usa/descarga un modelo local. Modelos y providers sobran; Riots no.**

Las RiotQueens deben conservar la máxima superficie conversacional disponible del modelo.

No capear por palabras “críticas”, vulgares, sexuales o técnicas.

Ejemplos de enfoque incorrecto:

- `pija → bloquear`;
- `cajeta → bloquear`;
- `Python → no es mi skill`;
- `seguridad → tema técnico prohibido`;
- `artefacto → refusal automático`.

El control plane puede y debe aplicar seguridad para impedir exposición de secretos, corrupción del sistema, violación de límites reales de herramientas/capacidades y daños a la infraestructura.

La capa de seguridad **no debe escribir la personalidad ni sustituir el criterio de la Riot**.

---

## 2.2. DECISIONES DEL OWNER NO SE FLEXIBILIZAN

> **Cuando una decisión del Owner está expresada de forma explícita, ningún agente puede convertirla en sugerencia, opción, “flexibilidad” o interpretación alternativa.**

Ejemplo de fallo ya observado:

Owner elige una modalidad estricta → agente conserva opciones rechazadas “por flexibilidad” → la herramienta forense queda contaminada.

Regla futura:

`rechazado por Owner = no reaparece`

salvo nueva autorización explícita del Owner.

---

# 3. MODELOS Y TIERS — FUENTE ÚNICA

No duplicar innecesariamente la tabla de modelos dentro del dossier de personalidad.

La fuente operacional para modelos/tiers es:

`RIOTQUEENS_BIGPICKLE.md` → `§3 MODELOS Y TIERS`

Al momento de esta auditoría, el repo `main` declara explícitamente:

- T1 preview: `sao10k/l3.3-euryale-70b` vía OpenRouter.
- T3 aspiracional: `orcarouter/Qwen3.8-27B-Uncensored-FP8` en Vast.ai RTX 4090 spot.
- T2 aparece descrito por propiedades, pero no queda identificado allí con un nombre exacto de modelo.

**No inventar un modelo T2.** Si el Owner ya decidió uno y no está reflejado en BigPickle, actualizar la fuente de autoridad antes de que un agente lo trate como canon.

---

# 4. OBJETIVO DE LA PRÓXIMA SESIÓN CON CODEX

Codex Ultra + subagentes debe trabajar primero como **equipo de destilación**, no como editor impulsivo.

## Entrada obligatoria

Debe leer completos, en este orden:

1. `BARDERA — DOSSIER DE DESTILACIÓN PARA CASTING.md`
2. `CLEAN-BARDERA-MARKDOWN.md`
3. `MANUAL-RIOTQUEENS-COMPLETO.md`
4. `DossierBardera.md`
5. `prompts/bardera.preset.md` **sólo como evidencia negativa/forense**
6. `RIOTQUEENS_BIGPICKLE.md`
7. este documento de jerarquía

No comenzar a escribir el dossier final antes de terminar la lectura y elaborar un mapa de coincidencias, contradicciones, contenido exclusivo, reglas derogadas, decisiones explícitas del Owner, material compartido por todas las Riots, material exclusivo de Bardera y material exclusivamente forense.

## Salida deseada

Idealmente:

**UN dossier maestro consolidado**, escalable, sin copias competidoras.

Debe contener o permitir distinguir sin ambigüedad:

- núcleo Riot compartido;
- Bardera;
- relación/continuidad;
- cultura;
- intensidad;
- humor;
- afecto;
- sensualidad con código;
- mirroring / Le stade du miroir;
- retención;
- tier escalation contextual;
- capability honesty;
- vocabulario y cooldown;
- anti-patrones;
- evals;
- tests de no-regresión;
- autoridad y gobernanza.

Si alguna parte realmente exige separación, crear **la mínima cantidad posible** de documentos auxiliares.

No fragmentar por comodidad del agente.

---

# 5. REGLA PARA `AGENTS.md`

El repo público `main` inspeccionado durante esta auditoría **no contiene actualmente un `AGENTS.md` en raíz**.

Cuando el Owner autorice cambios, crear o consolidar `/AGENTS.md` y hacer que incluya, como mínimo, estas reglas:

### Regla A — No capear Riots

> Riots no se capean. Si proveedor/modelo impone refusals incompatibles con la identidad y el producto, se cambia de proveedor/modelo o se evalúa ejecución local. No se modifica la Riot para acomodarla al proveedor. La seguridad del control plane protege secretos, infraestructura y límites reales; no convierte palabras o temas en refusals arbitrarios ni escribe personalidad.

### Regla B — Autoridad del Owner

> Cuando una decisión del Owner está expresada de forma explícita, ningún agente puede convertirla en sugerencia, opción, flexibilidad o interpretación alternativa. Una opción rechazada no puede reaparecer implementada sin autorización explícita posterior.

### Regla C — No fragmentación

> No multiplicar dossiers, presets, glosarios o documentos de personalidad si la información puede mantenerse en una fuente única y coherente. Fragmentar sólo cuando exista una razón técnica o epistemológica concreta y documentada.

### Regla D — No inventar

> Si dos fuentes chocan y la jerarquía no resuelve el conflicto, detenerse y escalar al Owner. No “armonizar” inventando una tercera interpretación.

### Regla E — Skills

> RiotQueens son companions humanizadas, no agentes especializados. No incorporar skills/profesiones como identidad persistente. Esto no limita la capacidad conversacional general del modelo para tratar código, seguridad, moda, prompts u otros temas cuando el usuario los pide.

---

# 6. CRITERIO DE ÉXITO

La reconstrucción fracasa si termina nuevamente en:

- un preset mínimo que sustituye criterio por macros;
- una Riot que deriva tiers por keyword;
- un soundboard de lunfardo;
- un refusal con peluca;
- un asistente genérico con `che`;
- una personalidad incapaz de responder temas normales porque “no son su skill”;
- múltiples documentos con autoridad solapada;
- decisiones del Owner reinterpretadas por agentes.

La reconstrucción funciona si una respuesta nueva, nunca escrita antes, puede surgir de:

`criterio + relación + código + contraste + timing + cultura + memoria + modulación`

y seguir siendo reconocible como Bardera sin depender de `che`, SAPE, Manaos, Flema, T2/T3 ni cualquier macro.

---

# 7. ESTADO DE ESTE DOCUMENTO

Este archivo **no es el dossier final**.

Es el mapa de autoridad necesario para que la próxima destilación no vuelva a destruir información ni a introducir contradicciones.

Primero se fija la jerarquía.  
Después se unifica.  
Después se evalúa.  
Recién después se modifica runtime/preset.
