# ADR 0001 — Queen inicial y routing de lanzamiento

**Estado:** aceptado
**Fecha:** 2026-08-08
**Enmendado:** 2026-08-10

## Contexto

El runtime recuperado usaba `vane` como identificador. El owner fijó RiotQueens.ai como marca y ratificó cinco Queens canónicas: Bardera, Tóxica Consciente, Gede, Rocha y Chela. Bardera es la Queen inicial y la única implementada actualmente. La conversación y la memoria existentes son estado efímero en proceso, la web ya usa `bardera` y no hay scopes ni datos durables que requieran migración.

Los landings conservan autoridad visual, compositiva y de ADN de diseño, pero sus asociaciones históricas Queen↔Tier no gobiernan el producto: no reactivan a La Rota ni congelan nombres, copy, pricing o claims superados.

## Decisión

- `bardera` es el `character_id` canónico del lanzamiento.
- El alias histórico se retira; el runtime registra únicamente `bardera` como Queen implementada.
- El frontend nuevo envía `bardera`.
- La API pública acepta únicamente Queens con prompt y fallback registrados y rechaza las demás antes de crear estado o invocar un proveedor.
- La ruta del modelo no forma parte del input público: `/v1/chat` selecciona `FAST_CHAT` del lado servidor.
- El flujo objetivo es landing → experiencia T0/free con Bardera → progresión independiente a tiers pagos cuando estén implementados.
- Ninguna Queen pertenece a un tier. La misma Queen puede continuar desde T0 hasta T3 sin cambiar su identidad básica.
- Web y API se publican bajo un único origen. Caddy enruta `/api/*` hacia FastAPI y el resto hacia Next.js.
- PostgreSQL y Redis no se ejecutan en producción hasta tener adaptadores reales que los consuman.

## Consecuencias

- No existen sesiones durables ni datos persistidos que requieran migración; el estado de prototipo desaparece al reiniciar el proceso.
- Los clientes soportados convergen en `bardera`; no hay evidencia de un consumidor vigente del identificador retirado.
- Bardera no equivale a T1; Tóxica Consciente, Gede, Rocha y Chela pueden incorporarse después sin asignarlas a tiers propios.
- Los identificadores aleatorios usados por la beta sólo separan estado efímero; no conceden identidad, permisos ni autenticación.
- El primer deploy es honesto: conversación y memoria siguen siendo estado en proceso.
