# Evaluaciones locales

Los resultados crudos de proveedores se escriben en `artifacts/evals/`, una ruta ignorada por Git. No se publican respuestas completas, claves, prompts internos ni datos de conversación.

Para compartir un resultado con otro agente o con ChatGPT web, publicar sólo un resumen sanitizado que incluya:

- Queen y batería;
- proveedor, modelo y modo;
- commit y fecha;
- cantidad de turnos;
- `hard_fails`, `capability_boundaries` e `infra_failures`;
- léxico cubierto;
- decisión `PASS`, `FAIL` o `PENDING_HUMAN_REVIEW`.

Un `HTTP 401`, timeout, cuota agotada o respuesta truncada es un problema de infraestructura/capacidad, no un fallo de personalidad. El harness lo informa como `INFRA_FAILURE` y termina con código distinto de `HARD_FAIL`. Debe repetirse con la misma batería antes de comparar modelos.
