# ADR 0002 — Límite de salida no confiable del modelo

**Estado:** aceptado

**Fecha:** 2026-08-09

**Enmendado:** 2026-08-10

## Contexto

Un proveedor puede devolver un bloqueo, una negativa genérica, su propia identidad o una respuesta técnica fuera de personaje. Si ese texto entra al historial como Queen, rompe continuidad y puede contaminar turnos posteriores. Un error de transporte tampoco debe aparecer como si lo hubiera dicho el personaje.

## Decisión

- La identidad de cada Queen y su fallback de continuidad son server-owned.
- La salida del proveedor se considera no confiable y atraviesa un validador determinista antes de almacenarse.
- Identidad de proveedor, fragmentos internos y negativas genéricas de guardrail invalidan la salida.
- Un bloqueo explícito o una salida inválida intenta el proveedor secundario configurado.
- Si ningún proveedor entrega una salida válida, el servidor devuelve y almacena un fallback corto registrado para esa Queen.
- Un fallo técnico sin respuesta de modelo permanece como voz de sistema; el frontend no inventa una burbuja de Queen.
- Prompts, memoria y scope nunca se reemplazan por texto devuelto por el proveedor.
- El router conserva provider, modelo, uso, latencia, validación y retries como diagnósticos internos; la respuesta pública de chat serializa únicamente el contenido aprobado para el usuario.

## Consecuencias

- Gemini, OpenRouter u otro proveedor pueden fallar sin apropiarse de la identidad del personaje.
- El historial conserva pares completos cuando el usuario recibe un fallback server-owned.
- La detección determinista no sustituye la política de producto ni autoriza contenido.
- Cada Queen nueva debe registrar prompt y fallback antes de publicarse.
- Cambiar de proveedor o fallback no altera el contrato público del chat ni expone backstage al navegador.
