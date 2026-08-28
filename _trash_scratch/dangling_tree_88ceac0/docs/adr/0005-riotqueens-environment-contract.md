# ADR 0005 — Contrato de entorno con prefijo RiotQueens

**Estado:** aceptado

**Fecha:** 2026-08-09

## Contexto

Un runtime histórico todavía usaba variables `COMPANION_*` aunque la marca, el repositorio y el producto canónico son RiotQueens.ai. Mantener ambos nombres activos crearía precedencias ambiguas, errores de despliegue y una dependencia conceptual con un producto anterior.

El primer despliegue público todavía no había ocurrido al adoptar este ADR, por lo que ese era el momento de corregir el contrato sin sostener aliases indefinidos.

## Decisión

- Toda configuración propia del runtime usa el prefijo `RIOTQUEENS_*`.
- Las variables canónicas de modelos son:
  - `RIOTQUEENS_MODEL_PROVIDER`;
  - `RIOTQUEENS_MODEL_BASE_URL`;
  - `RIOTQUEENS_MODEL_API_KEY`;
  - `RIOTQUEENS_MODEL_NAME`;
  - `RIOTQUEENS_MODEL_TIMEOUT_SECONDS`;
  - `RIOTQUEENS_MODEL_MAX_RETRIES`;
  - `RIOTQUEENS_MODEL_OMIT_FREQUENCY_PENALTY`;
  - `RIOTQUEENS_FALLBACK_MODEL_PROVIDER`;
  - `RIOTQUEENS_FALLBACK_MODEL_BASE_URL`;
  - `RIOTQUEENS_FALLBACK_MODEL_API_KEY`;
  - `RIOTQUEENS_FALLBACK_MODEL_NAME`.
  - `RIOTQUEENS_FALLBACK_MODEL_OMIT_FREQUENCY_PENALTY`.
- CORS, conversación y memoria siguen la misma regla: `RIOTQUEENS_CORS_ORIGINS`, `RIOTQUEENS_CONVERSATION_MAX_TURNS` y `RIOTQUEENS_MEMORY_MAX_PER_SCOPE`.
- El runtime no acepta aliases `COMPANION_*`. Un nombre único evita que dos secretos o proveedores compitan silenciosamente.
- Los nombres anteriores sólo pueden aparecer como contexto histórico explícito de una migración; no forman parte del contrato ni de la documentación operativa vigente.
- Los contratos internos continúan siendo independientes del proveedor: `openai` identifica el adaptador compatible, no una marca de producto ni un modelo concreto.
- El sufijo de proveedor incluido en un identificador remoto, por ejemplo `:ovhcloud`, es configuración de infraestructura y no se filtra al dominio.
- Un adaptador compatible puede omitir `frequency_penalty` mediante su flag explícito cuando una API lo rechace. No se infiere por nombre de modelo: exige smoke documentado y conserva el default para los demás proveedores.

## Consecuencias

- Todo `.env` local o de servidor debe migrarse antes de iniciar el runtime actualizado.
- Un despliegue que conserve únicamente `COMPANION_*` caerá al proveedor `mock`, comportamiento visible mediante `/v1/runtime/status`.
- Los secretos siguen siendo server-side, quedan fuera de Git y no usan nombres específicos del proveedor.
- Cambiar OpenRouter, Hugging Face o los modelos no requiere modificar el dominio ni volver a renombrar variables.
