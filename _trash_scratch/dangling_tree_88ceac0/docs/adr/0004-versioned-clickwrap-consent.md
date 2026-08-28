# ADR 0004 — Consentimiento clickwrap versionado y acceso +18

**Estado:** aceptado

**Fecha:** 2026-08-09
**Enmendado:** 2026-08-10

## Contexto

RiotQueens.ai es una experiencia de entretenimiento `+18` con personajes virtuales y ficticios que interactúan mediante inteligencia artificial. El producto necesita comunicarlo de forma breve, registrar una aceptación auditable y evitar que chat, cuenta o media premium dependan de una confirmación exclusivamente visual o almacenada sólo en el navegador.

La aceptación aporta evidencia, pero no reemplaza obligaciones de privacidad, seguridad, propiedad intelectual ni requisitos reforzados que pueda imponer una jurisdicción.

## Decisión

- La entrada protegida usa clickwrap con dos casillas sin premarcar:
  1. confirmación de 18 años y mayoría de edad aplicable;
  2. aceptación de Términos de Uso y Política de Privacidad.
- Los documentos se abren mediante enlaces visibles antes de aceptar.
- El botón de continuación permanece deshabilitado hasta completar ambas casillas.
- La landing informativa puede ser pública. Chat, creación de cuenta y premium requieren una aceptación vigente validada por backend.
- El cliente envía únicamente confirmaciones y versiones presentadas. El servidor genera timestamp e identidad del evento.
- El registro de aceptación es append-only y contiene como mínimo:
  - `acceptance_id`;
  - `user_id` autenticado;
  - `age_confirmed`;
  - `age_gate_version`;
  - `terms_version`;
  - `privacy_version`;
  - `accepted_at` en UTC;
  - digest de los documentos exactos aceptados;
  - evidencia técnica mínima definida por la política de privacidad.
- Las copias exactas de cada versión legal se preservan por hash.
- Un cambio material invalida la versión anterior para acceso futuro y solicita nueva aceptación.
- Consentimientos de marketing y notificaciones permanecen separados y opcionales.
- No se recolectan DNI, fecha de nacimiento ni biometría hasta que un requisito legal o una decisión explícita justifique una verificación de edad reforzada.
- El frontend refleja el estado; el backend concede o niega el acceso.

Contrato conceptual de entrada:

```json
{
  "age_confirmed": true,
  "terms_version": "2026-08-09",
  "privacy_version": "2026-08-09",
  "age_gate_version": "2026-08-09"
}
```

## Consecuencias

- La aceptación queda vinculada a una versión concreta y puede auditarse.
- Borrar cookies o modificar el frontend no concede acceso protegido.
- Auth real es requisito previo para asociar la aceptación a una identidad durable.
- Debe definirse una política de retención, acceso y eliminación compatible con las jurisdicciones habilitadas.
- Los claims públicos sobre privacidad, tracking, cookies, almacenamiento, venta de datos, pagos o cancelación requieren comportamiento real de la implementación, configuración real de producción y política o texto legal vigente cuando corresponda.
- La privacidad no cambia por tier salvo futura decisión explícita del owner.
- Una autodeclaración es el baseline del MVP, no una garantía universal de cumplimiento para todo país o categoría futura.

La política reutilizable de autorización para media está implementada como
`apps/api/app/domain/authorization.py`. Recibe una identidad ya verificada,
las versiones de clickwrap aceptadas y el tier; no implementa login, pagos ni
elige jurisdicción. La política falla cerrado ante identidad ausente, scope
distinto, aceptación vencida o tier insuficiente.
