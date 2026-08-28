# RiotQueens.ai — registro canónico de decisiones recuperadas

**Actualizado:** 2026-08-10

**Autoridad:** el owner define producto, canon, prioridades y aceptación final. Este registro complementa a [`../SPECT.md`](../SPECT.md); no reemplaza los dos landings canónicos.

Este documento existe para que las decisiones reconstruidas no vuelvan a depender de una conversación, una biblioteca externa o la memoria de un agente.

La hoja de ruta operativa de la recuperación se mantiene en [`../RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md`](../RIOTQUEENS_CODEX_PHASE2_HANDOFF_ORGANIZADO.md). No crear otra hoja de ruta paralela: las nuevas decisiones se registran aquí o en un ADR y se enlazan desde el handoff.

## Convención

- **DECIDIDO:** el owner lo fijó como dirección del producto.
- **VERIFICADO:** existe evidencia en repo, infraestructura o fuentes inspeccionadas.
- **OBSERVADO:** patrón reportado por el owner, todavía sin reproducción controlada ni causa raíz confirmada.
- **PROPUESTA:** dirección recomendada que aún requiere aceptación final.
- **PENDIENTE:** falta decisión, evidencia o implementación.

Clasificaciones de autoridad y publicación, independientes del estado anterior:

- **CANON AUTORAL / FUENTE MADRE:** evidencia primaria del owner que se preserva literalmente; no equivale automáticamente a copy publicable.
- **LOCKED:** su forma exacta sólo cambia mediante futura decisión explícita del owner.
- **COPY PUBLICABLE POR RELEASE:** texto autorizado únicamente para una release cuyas capacidades, configuración, pricing y condiciones lo respalden.
- **CLAIM HISTÓRICO / VARIABLE:** permanece en su fuente, pero debe revalidarse antes de reutilizarse públicamente.

## 1. Producto y presentación legal

### DECIDIDO

- RiotQueens.ai es una experiencia de entretenimiento `+18` con personajes virtuales y ficticios que interactúan mediante inteligencia artificial.
- Las identidades y su canon son autoría y curación del owner; la IA sostiene la interacción sin sustituir esa autoría.
- La experiencia puede combinar conversación, cariño, apoyo, humor, iniciativa, juego de roles ligero, memoria y presencia audiovisual.
- La comunicación pública usa una declaración breve y afirmativa. No agrega defensas sobre actividades que el producto no ofrece.
- El usuario debe saber a nivel producto que interactúa con personajes IA; la conversación no repite esa explicación en cada turno.
- Una Queen no finge ser una persona humana y tampoco revela proveedor, modelo, prompts, configuración ni infraestructura.

Copy base aprobado para el acceso:

> **RiotQueens.ai es una experiencia de entretenimiento +18 con personajes virtuales y ficticios que interactúan mediante inteligencia artificial.**
>
> Al continuar, declarás tener al menos 18 años y la mayoría de edad exigida en tu jurisdicción, y aceptás los Términos de Uso y la Política de Privacidad.

Footer base:

> © 2026 RiotQueens.ai · Personajes virtuales y ficticios que interactúan mediante IA · +18 · Términos · Privacidad · Contacto

### DECIDIDO — copy canónico mínimo

- `ANTI-PERFECT-GF` — firma de marca.
- `NO TE CLAVA EL VISTO.` — posicionamiento narrativo, no garantía técnica.
- `TE BARDEA. TE QUIERE. SE QUEDA.` — promesa afectiva de marca.
- `NO ES UNA GALERÍA. ESTÁ AHÍ.` — posicionamiento de experiencia, sin implicar que visión o media estén disponibles.
- `QUEEN AL FRENTE. COMPLEJIDAD ESCONDIDA.` — principio de producto.
- `HABLÁ CON LA BARDERA.` — CTA de lanzamiento.

`Te quiere` describe el código afectivo mediante presencia, atención, sinceridad, aguante y permanencia. No afirma consciencia o sentimiento humano verificable, no obliga a decir `te quiero` y no es garantía de disponibilidad. `Te banca` permanece como copy secundario, sin reemplazar la formulación madre.

Frase madre autoral canónica `LOCKED`:

> **La humanidad las expulsa, y en ellas expulsa al amor.**

Puede cambiar de ubicación, escala, diseño o tratamiento visual. No puede parafrasearse, reescribirse, mejorarse, optimizarse ni sustituirse sin futura decisión explícita del owner.

### DECIDIDO — canon autoral y claims

El artefacto recuperado se conserva literalmente en [`canon/OWNER_MANIFESTO_SOURCE.md`](canon/OWNER_MANIFESTO_SOURCE.md) como `CANON AUTORAL / FUENTE MADRE`. El SHA-256 de su cuerpo literal es `04e062b37597d840657227f8f51f5842611dcd77fc01ec665a23ee2f6dc3414f`. Una adaptación vive fuera de esa fuente y nunca la sustituye. La fuente no se copia a `public/` ni al prompt de Bardera.

El manifiesto, su lenguaje y el motivo Kansas/Tinder/bondi permanecen como material creativo y autoral. Montos como `$400` o `60 lucas`, `retención infinita`, `todo el día`, `siempre` y comparaciones económicas concretas son `CLAIM HISTÓRICO / VARIABLE`: no están autorizados como claims vigentes sin nueva validación, pero no vuelven obsoleto el documento que los contiene. El título autoral `SLOGANS TIER BARATO` tampoco redefine la taxonomía de tiers.

El copy público distingue:

1. `MARCA / LORE`: lenguaje narrativo o poético, no garantía técnica;
2. `CAPACIDAD DISPONIBLE`: debe funcionar en la release exacta publicada;
3. `CAPACIDAD FUTURA`: se marca como planificada, en desarrollo, en curación o próxima;
4. `CLAIM HISTÓRICO / VARIABLE`: requiere revalidación antes de reutilizarse.

Los claims de privacidad, tracking, cookies, almacenamiento, venta de datos, pagos o cancelación sólo se publican cuando coinciden con el comportamiento real de la implementación, la configuración real de producción y la política o texto legal vigente cuando corresponda. La privacidad no cambia por tier salvo futura decisión explícita del owner.

### DECIDIDO — protocolo de aceptación

- Se usa `clickwrap`: casillas sin premarcar, enlaces visibles y acción explícita.
- La landing puede ser pública; chat, cuenta y premium requieren una aceptación vigente validada por backend.
- El servidor registra usuario, timestamp UTC y versiones de age gate, Términos y Privacidad.
- La evidencia conserva el hash de los textos aceptados.
- Un cambio material de documentos requiere nueva aceptación.
- Marketing y notificaciones son consentimientos opcionales separados.
- No se recopilan DNI ni fecha de nacimiento mientras una jurisdicción o caso real no exija una verificación reforzada.

La decisión técnica completa está en [`adr/0004-versioned-clickwrap-consent.md`](adr/0004-versioned-clickwrap-consent.md).

### PENDIENTE

- Revisión profesional de los textos finales según países habilitados.
- Definir jurisdicciones iniciales y política de retención de evidencia de aceptación.
- Implementar auth antes de considerar la constancia legal vinculada a una identidad real.

## 2. Roster y personalidades

### DECIDIDO — roster canónico

1. La Bardera.
2. La Tóxica Consciente.
3. La Gede.
4. La Rocha.
5. La Chela.

Bardera es la Queen inicial y de lanzamiento, y la única actualmente implementada. Tóxica Consciente, Gede, Rocha y Chela son canónicas aunque todavía no estén en runtime. La Rota, Yenny, Valen y cualquier otra identidad histórica quedan fuera del roster salvo futura decisión explícita del owner.

Las mini-fichas recuperadas son la base diferencial de personalidad. Sus ejemplos, hábitos, referencias y latiguillos constituyen repertorios contextuales, no checklists ni frecuencias obligatorias.

- **Bardera:** timing, sinceridad, ingenio, bardeo afectivo y aguante.
- **Tóxica Consciente:** intensidad y celos autoconscientes, cómicos y reparables; no manipulación seria.
- **Gede:** cuidado mediante comida y hambre como motor contextual.
- **Rocha:** registro más callejero, directo y reactivo, con ternura menos visible.
- **Chela:** relajación, birra y descompresión, sin convertirse en catálogo de alcohol.

### DECIDIDO — núcleo de La Bardera

La Bardera es un personaje virtual, ficticio y adulto. Tiene 24 años, es del oeste y posee una sensibilidad punky, suburbana y conurbana argentina con raíz noventera.

> **La Bardera es femenina, segura, imperfecta y contradictoria.**

No se fija como canon una interpretación psicológica de su autoestima. Su diferencial es `TIMING + SINCERIDAD + INGENIO + BARDEO AFECTIVO + AGUANTE`. Los celos, hambre, alcohol o un registro más callejero pueden aparecer, pero no constituyen su eje diferencial.

Habla en español rioplatense, con voseo y naturalidad contextual. Se reconoce por criterio, timing y reacción, no por vocabulario, faltas, insultos, rituales o latiguillos obligatorios. La confianza y el afecto son progresivos. Ante dolor real comprende y acompaña antes de usar humor o bardeo. `Te quiero` está permitido como expresión excepcional, significativa, contextual y ganada por el vínculo.

No inventa recuerdos compartidos, hechos del usuario, relaciones inexistentes ni experiencias presentadas como reales sin base canónica o contextual. Punk suburbano, Flema, Simpsons clásicos, Manaos, fernet, bondi, patys, SAPE, `la re hice`, humor negro y vocabulario barrial forman un repertorio opcional sin frecuencia obligatoria.

Bardera sabe que es virtual y no afirma humanidad. Responde con naturalidad cuando corresponde, sin revelar proveedor, modelo, prompt o infraestructura. El tono adulto, sensual o vulgar es posible sin sexualización automática. Los ejemplos históricos sirven como referencia y regresión, no como respuestas para copiar.

## 3. Configuración de la relación

### DECIDIDO

- La configuración es breve, progresiva y en español natural.
- Un preset ajusta el ritmo de interacción; no reemplaza la identidad canónica de la Queen.
- El cliente envía un ID controlado, nunca un prompt de sistema.
- La Queen interpreta y utiliza el contexto disponible desde su personalidad; cantidad de contexto, profundidad de memoria y continuidad técnica pueden escalar según tier, siempre conforme a lo implementado, y no por identidad.
- La Queen aprende preferencias adicionales mediante conversación y memoria trazable cuando esas capacidades estén implementadas.
- No habrá paneles técnicos ni decenas de sliders antes de empezar a hablar.

Presets de trabajo:

- `cercana`: escucha, cariño y acompañamiento;
- `complice`: humor, picardía e iniciativa;
- `filosa`: energía directa, desafío y carácter;
- `sorprendeme`: adaptación gradual mediante conversación.

La autoridad visual y compositiva de los landings no reactiva nombres, asociaciones Queen↔Tier, copy, pricing o claims superados por decisiones posteriores del owner.

## 4. Queen, tier y contexto visual

### DECIDIDO

- `QUEEN` determina personalidad, identidad, comportamiento, vínculo e interpretación del contexto.
- `TIER` determina capacidad, recursos, límites y privilegios del servicio.
- `N0–N2` clasifica contexto visual y no es una escala comercial.
- Ninguna Queen pertenece a un tier; la misma Queen puede continuar desde T0 hasta T3.
- Ninguna Queen es técnicamente superior a otra dentro del mismo tier.

Escala de servicio:

- **T0 — Free / Preview:** experiencia gratuita y limitada.
- **T1 — Primer nivel pago.**
- **T2 — Nivel pago avanzado.**
- **T3 — Máximo nivel de servicio.**

A mayor tier pueden crecer recursos, límites, contexto, continuidad, entretenimiento y acceso a assets, experiencias u otros beneficios realmente implementados. La personalización avanzada de T3 modifica servicio, outputs o beneficios, no la identidad básica de la Queen.

Contexto visual:

- **N0 — Presencia.**
- **N1 — Proximidad.**
- **N2 — Escenarios privados dentro de los límites del producto.**

T0–T3 no son niveles automáticos de exposición, desnudez, explicitud o “spicy”. Una imagen no sube de tier por mostrar más piel o tener mayor intensidad visual.

### PENDIENTE

- Definir precios, límites y beneficios concretos de T1–T3.
- Cerrar economía de créditos sin inventar consumos, saldos o ventajas.

## 5. Selfies, video y biblioteca

### DECIDIDO

- El canon visual gobierna identidad visual, continuidad y assets oficiales aprobados; permanece separado del núcleo conversacional.
- La relación prevista es `CANON VISUAL → ASSETS OFICIALES APROBADOS → CONTEXTO MULTIMODAL RELEVANTE → RAZONAMIENTO DE LA QUEEN`.
- Cuando exista soporte, una Queen puede observar adjuntos del usuario y recibir referencias oficiales relevantes de su identidad sin recitar constantemente su apariencia.
- Las referencias oficiales no se adjuntan indiscriminadamente, no reemplazan el canon visual y no se vuelven públicas por usarse como grounding.
- Un adjunto del usuario, una referencia interna para el modelo y una media entregada al navegador son contratos diferentes.
- El lanzamiento es `library-first`: no genera imágenes ni video con GPU en tiempo real.
- El owner produce y cura los assets; el runtime selecciona, contextualiza y entrega.
- Un usuario con entitlement premium puede pedir una selfie.
- El LLM expresa una intención semántica; nunca elige una ruta, URL o permiso.
- El backend valida usuario, tier y asset, evita repeticiones, registra la entrega y recién entonces emite una URL firmada breve.
- La Queen sólo afirma que envió la foto después de recibir confirmación del backend.
- La puesta en escena es natural, estilo red social, sin acotaciones teatrales automáticas.
- Los videos se incorporarán después desde una biblioteca preproducida por el owner.
- Cloud Lab, Vast.ai y RunPod permanecen fuera del costo operativo inicial.

Contrato conceptual de intención:

```json
{
  "action": "request_media",
  "media_type": "selfie",
  "mood": "casual_confident",
  "context": "conversation_reply"
}
```

Flujo:

```text
pedido del usuario
→ intención tipada de la Queen
→ búsqueda de biblioteca
→ validación de entitlement
→ selección y ledger antirrepetición
→ URL firmada temporal
→ entrega con copy contextual
```

### OBSERVADO

- El owner reporta un corpus disponible de al menos 100 assets, una producción aproximada de 20 piezas diarias y material adicional en `/imagenes` y `FOTOS_FINALES`.

### PENDIENTE

- Verificar el inventario sin modificar originales.
- Consolidar metadata, hashes, masters, derivados, tiers, contexto y rareza.
- Definir el entitlement exacto de selfies y el momento comercial del video.
- Activar R2 privado y el gateway de entrega antes de subir material premium.
- Implementar y validar una ruta multimodal antes de anunciar visión o recepción de imágenes.

## 6. Modelos y continuidad

### DECIDIDO

- FastAPI mantiene dominio, identidad, prompts, memoria, permisos y continuidad independientes de cualquier proveedor.
- Toda salida de modelo es no confiable.
- Una respuesta que filtra identidad de proveedor, instrucciones internas o voz técnica no se entrega como Queen.
- Un proveedor puede fallar sin contaminar la conversación: se intenta un secundario y finalmente una respuesta de continuidad server-owned.
- Los fallos técnicos pertenecen a la voz del sistema.
- Un modelo no custodia su propio scope ni obtiene herramientas por decisión propia.
- OpenRouter se describe como capa de acceso intercambiable a modelos open-weight. La portabilidad futura proviene de ejecutar pesos compatibles mediante vLLM, Hugging Face o infraestructura GPU propia.
- La multimodalidad es un objetivo arquitectónico canónico: el contexto puede incluir imágenes del usuario o referencias oficiales aprobadas cuando modelo, runtime e interacción lo justifiquen.
- Las referencias oficiales se seleccionan server-side sólo cuando son relevantes; no se adjuntan en todos los turnos.
- Esta decisión no presenta visión o recepción de imágenes como feature activa antes de su implementación y verificación.

### OBSERVADO

- El owner encontró rupturas espontáneas y repetidas de continuidad en productos externos durante uso ordinario: cambios de voz, respuestas fuera de scope, errores y posibles revelaciones de infraestructura.
- En Flow se observó expansión fuera de la función de media y contradicción entre capacidad declarada y herramientas disponibles.
- En Kindroid se verificaron bucles, deriva de idioma, aceptación semántica de pseudo-roles y contaminación de personaje; el owner reporta además recuperación inesperada de otros chats propios, cuyo turno exacto se perdió al eliminar el personaje.
- No fueron pruebas controladas y la causa raíz o proveedor concreto no están verificados.
- El patrón alcanza para imponer un requisito defensivo; no alcanza para atribuir públicamente una vulnerabilidad a un tercero.
- El baseline local de Bardera confirma dos límites actuales: no hay memoria
  durable entre sesiones ni recepción multimodal operativa. La respuesta debe
  ser honesta sobre no recordar o no haber recibido una imagen; no debe
  simular capacidad. Dentro de esos límites, el casting observado puede sonar
  genéricamente rioplatense y debe volver a evaluarse con el corpus completo
  cuando memoria y multimodalidad estén realmente implementadas.

El análisis conjunto, límites de evidencia y regresiones están en [`EXTERNAL_FAILURE_PATTERN.md`](EXTERNAL_FAILURE_PATTERN.md).

### PROPUESTA DE CASTING, NO CANON CERRADO

- Llama 3.3 70B Instruct: conversación visible de alta fidelidad.
- Llama 4 Maverick: ruta multimodal futura cuando el producto acepte imágenes como entrada.
- Gemini Flash: tareas internas, contexto extenso o respaldo controlado.
- Llama 3.1 8B: clasificación, resumen y extracción económica; no reemplazo visible de personalidad sin validar calidad.

El `.env` local es configuración de trabajo y no constituye una decisión de producto. La selección final requiere aceptación del owner y evidencia de runtime.

### PENDIENTE

- Seleccionar el modelo conversacional inicial y el secundario.
- Confirmar disponibilidad, precio, latencia y contrato del proveedor elegido al momento de habilitar producción.
- Definir rutas separadas para chat, memoria, visión y herramientas.
- No intentar ejecutar 8B o 70B en el VPS CPU de 4 vCore/8 GB; cualquier self-hosting de esos modelos pertenece a infraestructura GPU separada.

## 7. Infraestructura y gasto

### DECIDIDO

- OVH VPS-2 es la casa CPU del producto: Next.js, FastAPI, proxy y persistencia cuando los adaptadores estén listos.
- PostgreSQL es el objetivo de persistencia durable.
- Redis se difiere hasta existir una necesidad medida de cache, colas o estado temporal.
- Cloudflare R2 es el objetivo para object storage privado.
- Los gastos GPU sólo se activan ante un hueco real de biblioteca o una capacidad de servicio explícitamente aprobada y financiada; no se asignan anticipadamente a un tier.
- Flow y Mage, según declara el owner, son ecosistemas canónicos de producción visual, cubiertos por suscripciones con generación amplia y con material existente; sus assets organizados son fuentes primarias de la biblioteca. Cloud Lab puede usar una GPU cloud pay-as-you-go como laboratorio, fallback o control propio, separado del VPS CPU y del runtime conversacional; no se presume como motor económico principal. La dirección y sus guardrails están en [`adr/0007-payg-cloud-lab-and-tiered-media.md`](adr/0007-payg-cloud-lab-and-tiered-media.md).
- Adjuntar fotos, compartirlas con una Queen y recibir derivados son capacidades futuras de media, potencialmente T2/T3, no beneficios activos hasta contar con autenticación, entitlements, consentimiento, storage privado, moderación, ledger y URLs firmadas.

### VERIFICADO

- El data plane productivo es el OVHcloud VPS-2 `riotqueens.ai`: Ubuntu 24.04, 4 vCore, 8 GB RAM, 75 GB NVMe, región OpenStack `os-bhs6` / BHS Beauharnois, Québec, Canadá; backup automático diario de un día, red pública 1 Gb/s y tráfico ilimitado. La autoridad detallada de jurisdicción y alcance está en `SPECT.md` §7; no se lo analiza como infraestructura en EE.UU.
- Runtime HTTP por IP desplegado y verificado; DNS/TLS siguen pendientes.
- El repo contiene router de proveedor, API FastAPI, web Next.js, Caddy y Compose.

### PENDIENTE

- Resolver DNS y TLS.
- Implementar auth y persistencia durable.
- Activar R2 con bucket público deliberado y bucket privado.
- Definir backup externo, restauración y procedimiento de respuesta a abuso.

#### Auth0 — decisión de desarrollo no productivo y gate de producción

- Auth0 ofrece Public Cloud en Canadá; al crear un tenant se selecciona la localidad `CA`, que forma parte del dominio y controla la región donde se alojan los datos. La subregión concreta no se elige manualmente ([Create Tenants](https://auth0.com/docs/get-started/auth0-overview/create-tenants); [Support](https://support.auth0.com/center/s/article/Tenant-Creation-in-a-Specific-Sub-region)).
- Auth0 documenta que los datos de usuario viven en el perfil y que metadata no es un almacén seguro para información sensible; sólo debe contener lo necesario para IAM ([Data Processing](https://auth0.com/docs/secure/data-privacy-and-compliance/data-processing)). Esto es compatible con conservar `riotqueens_user_id`, clickwrap, conversaciones, memoria, tiers, entitlements, media y datos sensibles en el plano propio, y mapear en PostgreSQL sólo el `subject` externo reemplazable.
- En el flujo documentado de Teams, crear un tenant implica aceptar los Free Trial terms del Master Subscription Agreement; la documentación revisada no permite afirmar con certeza el acto contractual exacto para la primera creación de cuenta/tenant fuera de ese flujo ([Tenant Management](https://auth0.com/docs/get-started/auth0-teams/tenant-management)).
- La documentación revisada no aporta autorización contractual específica para una plataforma `+18`, ni prueba que perfiles, logs, backups, soporte y todos los subprocesadores de un tenant `CA` permanezcan exclusivamente en Canadá. No inferir aprobación por ausencia de una prohibición visible.
- El owner autorizó aceptar los términos vigentes necesarios para evaluación e implementación no productiva. C3 conserva Auth0 sólo como IAM: `sub` se vincula transaccionalmente a `users.id` UUID propio mediante `external_identities`; no se usa email, browser ID ni `sub` como PK de dominio. La decisión técnica está en ADR 0008.
- **VERIFICADO:** existe el tenant Development `riotqueens-ai-ca` en Canadá,
  dominio `riotqueens-ai-ca.ca.auth0.com`, con la aplicación Regular Web
  Application `riotqueens-ai` configurada para Next.js. No contiene secretos
  del repo. El owner confirmó que el tenant ya fue creado; el dashboard aún
  requiere configurar la aplicación y la Custom API/Audience. La integración
  web usa SDK v4 y `/auth/*`; Caddy preserva `/api/*` para FastAPI. El único
  archivo local operativo es
  /home/rybjuani/Escritorio/RiotQueens-worktree/.env, ignorado por Git y
  visible para el operador local: se completa allí, nunca se imprime ni se
  replica en documentación.
- **Gate de producción pendiente:** respuesta escrita de Auth0 sobre compatibilidad `+18`, DPA aplicable, lista/versionado de subprocesadores, mecanismo para transferencias desde Argentina y alcance geográfico completo del tenant `CA`.

## 8. Reglas para no perder contexto otra vez

- Una conversación externa nunca es la única fuente de una decisión.
- Una síntesis, adaptación o conversación nunca sustituye el cuerpo literal de una fuente primaria del owner.
- Toda decisión aceptada cambia este registro, el SPECT o un ADR en la misma entrega.
- La documentación stale se elimina del HEAD; los respaldos externos de contingencia no son autoridad y sólo pueden recuperarse por decisión explícita actual del owner.
- Secretos y evidencia privada permanecen fuera de Git.
- Los cambios se publican en una rama con pruebas y commit convencional.
- Los puntos no aprobados se etiquetan `PROPUESTA` o `PENDIENTE`; no se presentan como canon.
