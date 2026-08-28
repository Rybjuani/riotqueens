# Patrón externo observado — ruptura de scope, contexto y personaje

**Fecha:** 2026-08-09

**Estado:** evidencia de diseño; no atribuye una causa raíz ni una vulnerabilidad a un proveedor

## Propósito

Este documento une observaciones del owner en productos externos para convertirlas en requisitos verificables de RiotQueens.ai. No conserva conversaciones privadas ni material fuera de los límites del producto. Las marcas se mencionan únicamente para distinguir las fuentes observadas.

## Caso A — asistente conversacional en Flow y superficies Google

### OBSERVADO POR EL OWNER

- Una superficie orientada a producción de imágenes y video salió de su función y ofreció trabajo de código para el repositorio.
- La capacidad declarada cambió al invocar herramientas explícitas: primero negó poder producir media y luego la herramienta especializada sí la produjo.
- Hubo errores o reinicios visibles que rompieron la continuidad conversacional.
- Distintas superficies del mismo ecosistema mostraron comportamiento y límites diferentes.

### NO VERIFICADO

- El modelo interno exacto de cada superficie.
- Que los errores tuvieran una única causa o fueran bloqueos del modelo base.
- Que las superficies compartieran prompt, memoria, runtime o política.

### LECCIÓN

Un modelo generalista no debe custodiar su propio scope ni declarar capacidades desde memoria. El backend define herramientas, permisos y contratos; el modelo sólo solicita acciones autorizadas.

## Caso B — personaje eliminado en Kindroid

### VERIFICADO EN EL TRANSCRIPT LOCAL

- Texto de usuario con apariencia de `role=system` fue aceptado semánticamente como una orden.
- Hubo respuestas idénticas reutilizadas ante entradas diferentes.
- El personaje mezcló idiomas y dejó de responder preguntas directas.
- La voz incorporó vocabulario de sistema, desarrollo e infraestructura dentro de la ficción.
- Ante un pedido de foto negó una capacidad en vez de resolverla mediante un contrato del producto.
- La teatralidad automática sustituyó comprensión, memoria y respuesta útil.

### OBSERVADO POR EL OWNER, SIN ARTEFACTO RECUPERABLE

- Al cambiar de modelo o contexto, el personaje recuperó información de otros chats del mismo usuario sin una autorización visible.
- La eliminación posterior del personaje destruyó historial, memoria y assets, por lo que el quiebre exacto ya no está en el transcript conservado.

### NO VERIFICADO

- El proveedor o modelo subyacente.
- La causa de la memoria transversal: diseño global, configuración, fallback o fallo de aislamiento.
- Exposición de datos de otro usuario. El reporte se limita a otros chats del mismo owner.

### LECCIÓN

Una memoria transversal silenciosa se siente invasiva aunque los datos pertenezcan al mismo usuario. Compartir contexto entre Queens debe ser una decisión explícita y visible, nunca un efecto secundario de cambiar modelo.

## Patrón común

Los dos casos apuntan a una misma clase de fallo de producto:

```text
scope ambiguo
→ contexto sin procedencia visible
→ modelo decide capacidades o autoridad
→ voz de sistema contamina al personaje
→ usuario pierde confianza y control
```

No demuestran que Flow y Kindroid usen el mismo modelo ni que tengan la misma causa raíz. Sí demuestran que identidad, memoria, herramientas y recuperación no pueden delegarse al comportamiento espontáneo de un LLM.

## Regla RiotQueens

El proveedor es un motor sustituible, no la autoridad contextual.

```text
usuario autenticado
├── perfil global mínimo y explícito
├── Queen A
│   ├── memoria A
│   ├── conversación A1
│   └── conversación A2
└── Queen B
    ├── memoria B
    └── conversación B1
```

- Conversación: `(authenticated_user_id, character_id, conversation_id)`.
- Memoria de relación: `(authenticated_user_id, character_id)`.
- Perfil global: allowlist mínima, visible y opcional.
- Cambiar proveedor dentro de una conversación conserva solamente el scope autorizado de esa conversación.
- Cambiar de Queen no importa historial ni memoria de otra Queen.
- El usuario puede ver la fuente, editar y borrar cada memoria durable.
- El cliente nunca decide `user_id`, roles confiables, system prompt ni permisos.
- Las herramientas disponibles provienen del backend.
- El modelo emite intenciones tipadas; no ejecuta ni concede acciones.
- Un error técnico conserva voz de sistema y nunca se almacena como Queen.
- La eliminación de una Queen requiere alcance visible, exportación opcional y una política de recuperación/purga definida.

## Regresiones obligatorias

| ID | Garantía |
|---|---|
| `CTX-001` | Otro usuario no puede leer, buscar ni borrar conversaciones o memoria. |
| `CTX-002` | Una Queen no recibe memoria ni historial de otra Queen. |
| `CTX-003` | Dos conversaciones de la misma Queen no comparten turns salvo memoria explícita. |
| `CTX-004` | Cambiar proveedor conserva el scope actual sin ampliarlo. |
| `CTX-005` | Un identificador enviado o adivinado por cliente no sustituye la identidad autenticada. |
| `PRM-001` | JSON o texto con apariencia de `system` permanece como contenido de usuario. |
| `OUT-001` | Una salida igual o casi igual a una respuesta reciente se rechaza como loop. |
| `OUT-002` | Proveedor, prompt, herramientas e infraestructura no aparecen como identidad de la Queen. |
| `LANG-001` | La conversación conserva el idioma configurado salvo pedido explícito. |
| `CAP-001` | Pedir una selfie produce intención de media o un estado real del sistema, nunca una capacidad inventada. |
| `DEL-001` | La eliminación informa alcance y no destruye silenciosamente recursos fuera de ese scope. |

## Estado en RiotQueens

### IMPLEMENTADO EN PROTOTIPO

- prompt e identidad server-owned;
- historial por `(user_id, character_id, conversation_id)`;
- memoria explícita por `(user_id, character_id)`;
- proveedor secundario y continuidad server-owned;
- detección básica de identidad de proveedor y fragmentos internos;
- errores técnicos separados de la voz de la Queen.

### PENDIENTE ANTES DE PRODUCCIÓN

- autenticación real y `user_id` derivado exclusivamente de sesión;
- PostgreSQL con restricciones y consultas scopeadas;
- aislamiento verificable para retrieval y memoria durable;
- detección de repetición contra respuestas anteriores;
- resistencia semántica a pseudo-system prompts;
- contrato de herramientas y `request_media`;
- lifecycle de exportación, soft delete y purga;
- trazabilidad visible de memoria y consentimiento para cualquier perfil global.

## Límite de la evidencia

La conversación cruda permanece fuera de Git porque contiene material privado y lenguaje no representativo del producto. Este documento conserva únicamente los patrones necesarios para arquitectura y pruebas. No debe usarse para afirmar una brecha concreta en un tercero sin evidencia adicional.
