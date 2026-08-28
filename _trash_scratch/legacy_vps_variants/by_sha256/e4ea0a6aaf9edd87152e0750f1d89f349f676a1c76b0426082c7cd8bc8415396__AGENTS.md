# RiotQueens.ai — reglas para agentes

Antes de modificar producto, leer [`SPECT.md`](SPECT.md), este archivo y el contexto específico de la tarea. La interfaz y el copy público usan español natural; código, identificadores y contratos internos usan inglés.

## Autoridad

- El owner define producto, prioridades, canon y aceptación final.
- Los dos landings mandan conjuntamente.
- `docs/reference/visual/Riotqueens-Ai-Landing-Mock.html` es autoridad visual, compositiva y de ADN de diseño dentro del alcance reconocido por las fuentes vigentes; no gobierna roster, asociaciones Queen↔Tier, voz o personalidad canónica, no reactiva identidades históricas y no congela copy, pricing o claims superados por decisiones posteriores del owner.
- `docs/reference/visual/Reiniciando-chat-anterior.html` gobierna continuidad, interacción y flujo.
- `RiotQueens_logo_design_202608082344.jpeg` es el logo oficial bloqueado; la copia web canónica tiene SHA-256 `e47df47761cdee8da0b7674b0bdb8f35a71086c24474a33d2b496de67ad3e3b1`.
- No redibujar, reinterpretar, recortar destructivamente ni reemplazar el logo sin decisión expresa del owner.
- No reinterpretar, homogeneizar ni reemplazar ninguno con una estética genérica.
- Ante una contradicción material entre ambos, documentarla y escalarla al owner.
- `SPECT.md` es la autoridad funcional y arquitectónica vigente.
- `docs/DECISION_REGISTER.md` conserva decisiones recuperadas, propuestas y pendientes sin convertirlas automáticamente en canon.
- La documentación stale se elimina del HEAD; un respaldo externo de contingencia no es autoridad y sólo puede recuperarse por decisión explícita actual del owner.

## Producto y lenguaje

- Mantener RiotQueens.ai como marca y a las Queens como personajes virtuales ficticios y originales.
- Usar `+18` como señal legal pública, sin aclaraciones defensivas innecesarias.
- Evitar vocabulario heredado que sugiera servicios o contenidos que el producto no ofrece.
- No presentar una biblioteca precargada como generación en tiempo real.
- No convertir la experiencia en catálogo genérico, dashboard corporativo ni configuración técnica expuesta al usuario.
- Toda voz tiene dueño: Queen o sistema.

## Arquitectura

- Mantener el dominio independiente de proveedores LLM, storage y GPU mediante interfaces y adaptadores.
- No cambiar límites, contratos o arquitectura sin crear o actualizar un ADR vigente.
- Conservar prompts de sistema, autorización y scopes confiables del lado servidor.
- Tratar toda salida LLM como no confiable: identidad, fallback y continuidad de cada Queen son server-owned.
- Cada Queen publicable debe registrar prompt y fallback; un proveedor nunca puede presentarse con identidad propia.
- Diferenciar estado en proceso, cache y persistencia durable; nombrarlos honestamente.
- No agregar infraestructura por anticipación: primero medir el caso.

## Seguridad y medios

- Nunca commitear secretos, datos personales, originales privados, referencias de identidad ni workflows sensibles.
- No usar nombres, imágenes o datos de personas reales en fixtures.
- Trabajar con copias verificadas, previews y derivados; no sobrescribir masters.
- Los assets de `FOTOS_FINALES` que entren al repo son copias provisionales hasta la selección final del owner y deben figurar en `docs/ASSET_PROVENANCE.md`.
- Preservar trazabilidad de memoria, configuración, créditos, medios y linaje de assets.
- Nada premium llega al navegador antes de autorización backend.
- Todo archivo dentro de `apps/web/public/` debe figurar con hash en `config/public-media.json` y estar marcado no premium.
- No servir directorios personales desde el VPS.

## Flujo de trabajo

1. Verificar repo, branch, commit, estado y baseline.
2. Leer el SPECT y contratos afectados.
3. Separar `VERIFICADO`, `INFERENCIA`, `PROPUESTA` y `PENDIENTE`.
4. Agregar un ADR si cambia una decisión arquitectónica.
5. Implementar una pieza pequeña con pruebas.
6. Ejecutar lint, build y tests proporcionales al cambio.
7. Auditar diff, seguridad y documentación.
8. Trabajar en rama y usar commits convencionales.

No convertir al owner en QA manual. Para acciones reversibles y dentro del alcance, avanzar con autonomía y dejar evidencia auditable.

## Control de macrofase

Antes de devolver el control al owner:

- verificar la macrofase activa y sus criterios de salida en el handoff vigente;
- un commit o test aprobado no es por sí solo un límite de macrofase;
- si queda trabajo seguro y ejecutable dentro de la macrofase activa, continuarlo;
- no elevar un subproblema descubierto a prioridad de proyecto sin contrastarlo con el roadmap canónico;
- escalar sólo bloqueos reales o decisiones de producto, canon, gasto, legalidad o efectos irreversibles.

## Anticontaminación histórica

- Git history, commits antiguos, ramas stale, archivos borrados y respaldos externos no son autoridad de producto.
- No reconstruir producto, políticas, roster, capacidades, legalidad o arquitectura desde historial Git.
- Consultar historia sólo para debugging, procedencia o recuperación forense cuando la tarea lo requiera explícitamente.
- Si la historia contradice HEAD, SPECT o un ADR vigente, manda la autoridad vigente.
- No revivir nombres, productos, features o decisiones históricas por encontrarlos en commits.
