# Pipeline de curaduría y casting de Queens

**Estado:** PROPUESTA OPERATIVA basada en evidencia auditada el 2026-08-15.

Este documento describe cómo transformar material autoral del owner en un perfil de Queen reproducible. No reemplaza `SPECT.md`, no convierte una conversación de NotebookLM en canon automático y no pone fuentes privadas en el navegador.

## Intención de producto recuperada

Qwen Full-Stack dejó una solución editorial y estructural que debe reciclarse: la marca RiotQueens es anti-perfect-gf, punk/glam, intensa, irreverente y afectiva; la Queen está al frente, el sistema queda detrás; el landing conduce a una experiencia de presencia y conversación, no a un catálogo técnico. El diseño puede reutilizar tokens, composición, jerarquía, altar/manifiesto, marquee, estados de disponibilidad, tarjetas de Queen y flujo hacia chat.

La misión operativa es ofrecer compañía ficticia con identidad, voz, continuidad y aguante. La visión es escalar varias Queens sin homogeneizarlas: comparten una esencia RiotQueens, pero cada una conserva su registro, referencias, límites, glosario y forma de vincularse.

Los claims, roster histórico, precios, tiers y cualquier promesa de visión/generación se revalidan contra `SPECT.md` antes de publicarse. El HTML de Qwen es una fuente de ADN visual y estructural, no una autoridad para reactivar `La Rota` ni copy superado.

## Flujo repetible por Queen

1. **Recolección:** reunir fuentes del owner, referencias culturales, imágenes derivadas y manifiestos. Registrar ubicación externa, hash, fecha y permisos en `docs/canon/QUEEN_SOURCE_REGISTER.md`.
2. **Curaduría NotebookLM:** cargar fuentes en un notebook separado por Queen; pedir autodescripción de forma de ser, hablar, pensar, límites, escenas y ejemplos. Exportar informes, no tomar una respuesta aislada como verdad.
3. **Estructuración:** convertir los informes en `identity.md`, `voice.md`, `glossary.md`, `boundaries.md` y `eval.md`. Separar CANON AUTORAL, INFERENCIA, PROPUESTA y PENDIENTE.
4. **Casting:** ejecutar la batería de modismos de esa Queen contra cada modelo/configuración. Medir voz, falso positivo, rechazo fuera de contexto, fuga de identidad y continuidad.
5. **Aprobación:** `PASS` sólo si la configuración aprueba los umbrales de la batería y una revisión humana del perfil; el resultado debe registrar modelo, proveedor, parámetros, commit y fecha. Un fallo de credencial o transporte es `INFRA_FAILURE`, no un fallo de voz.
6. **Runtime:** sólo los artefactos aprobados llegan al adaptador server-owned. El modelo nunca elige identidad, prompt, ruta de asset ni permiso.

## Regla de benchmark

La batería de La Bardera es la primera regresión porque ya existe un corpus y demostró el problema de falso positivo con modismos. Su aprobación habilita una configuración para Bardera; para Tóxica Consciente, Gede, Rocha y Chela se necesitan glosarios y baterías propias. Compartir el modelo no comparte la personalidad.

## Estado actual

- Bardera: perfil conversacional runtime y batería inicial implementados; sigue en calibración real de proveedor.
- Las otras cuatro Queens: roster canónico y previews provisionales; voz y glosario independientes pendientes.
- NotebookLM: flujo validado por evidencia local (`barderainvernadero.png` y `MANIFIESTO_BARDI.pdf`); export autenticado del notebook compartido pendiente.
- Multimodalidad: objetivo arquitectónico; no está publicada como feature.
