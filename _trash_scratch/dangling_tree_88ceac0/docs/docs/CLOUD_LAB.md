# Cloud Lab y media multimodal

**Estado:** PROPUESTA OPERATIVA DOCUMENTADA; no es una capacidad publicada.

## Qué se recupera de la propuesta

La carpeta externa `/home/rybjuani/Escritorio/propuesta/` describe un laboratorio visual efímero: levantar una GPU cloud potente sólo durante un trabajo, ejecutar un workflow de ComfyUI con una imagen de referencia, identidad facial, pose, prompt y upscale, descargar derivados y apagar el pod. La intención del producto es que el owner siga siendo curador de las Queens y de sus perfiles; la generación ayuda a producir material visual consistente, no reemplaza la selección humana ni convierte una imagen en canon automáticamente.

La auditoría también recuperó una captura histórica de una interfaz de edición. Puede servir para estudiar estructura de edición y flujo, pero no gobierna marca, roster, voz, tier ni copy actuales.

Los archivos externos quedan fuera del repo porque pueden contener material privado o de trabajo. Sus hashes auditados son:

| Fuente | SHA-256 | Clasificación |
|---|---|---|
| `10_after_send_4.png` | `8339f95479b26da5cc2e5b3dee6bd8714a8792bf93bf9e089da66fcdd9ff9299` | referencia histórica de estructura |
| `comfyui_workflow_dark_neon.jpg` | `c7d72730d9c959d75ef27e54bf70adc9a4072b467c0fa4fe71d7a339570bbc1c` | diagrama de workflow, no ejecutable por sí mismo |
| `runpod_deployment_ui.jpg` | `af76831b35dc146084a6eab12efc9697033ad71ae1ab6b7df3a800850c8a05c4` | evidencia visual histórica de despliegue |
| `📕-DESCARGAR-PDF-Riot-Queens-Cloud-Lab.pdf` | `bb3f8f57a3913327894faa4c373fd839e9932272a22128103037e07e1d69a944` | propuesta de laboratorio |
| `📕-DESCARGAR-PDF-V2-Guía-Visual-Completa.pdf` | `25af98ee74e1d40ca9c910f40747b298b692248fcd590aeba9ac13f9984b92cc` | propuesta de workflow y costos |

Los tiempos, precios y nombres de instancias de esas capturas son `CLAIM HISTÓRICO / VARIABLE`. El owner declara además que Flow y Mage son ecosistemas canónicos de producción visual, ya cubiertos por suscripciones y con material masivo existente. Por eso el costo marginal de una selfie no debe modelarse automáticamente como GPU × segundos × imagen: primero se debe respetar ese patrimonio, clasificarlo y medir los límites reales de esas suscripciones.

## Decisión de arquitectura

El VPS actual es CPU y continúa siendo la casa del producto: API, autorización, colas, adaptadores, storage y entrega. El Cloud Lab es un proveedor opcional de producción o procesamiento visual, separado del runtime conversacional. No se instala una GPU local ni Ollama en el VPS para resolver este caso.

La primera versión del producto sigue siendo `library-first`: assets preproducidos, curados y trazables. Flow y Mage son fuentes canónicas de producción visual y rutas primarias para aprovechar el material ya creado. Cloud Lab queda como laboratorio, fallback, control propio de workflows/provenance y opción de independencia; no se asume que sea el motor económico principal. RunPod y Vast son candidatos intercambiables para una futura implementación pay-as-you-go, sólo si una medición demuestra que aportan valor frente a los ecosistemas canónicos.

## Media y tiers

La posibilidad de adjuntar una foto, compartirla con una Queen y recibir un derivado generado es una capacidad futura de media multimodal. Puede formar parte de beneficios T2/T3, pero el tier sólo otorga una capacidad cuando entitlements, autorización, política y economía estén implementados. No se debe prometer como disponible por existir un workflow.

El flujo esperado es:

1. el usuario solicita una operación y el backend verifica cuenta, +18, tier, créditos y consentimiento;
2. el cliente sube el archivo a storage privado mediante URL firmada, nunca al filesystem del VPS ni a `public/`;
3. el servidor crea un manifiesto de trabajo con Queen, scope, propósito, retención y referencias autorizadas;
4. el adaptador levanta una GPU cloud sólo si el trabajo fue aprobado, ejecuta el workflow versionado y aplica límites de tiempo, tamaño y costo;
5. el backend valida resultado, provenance, política y permisos, guarda un derivado privado y registra el ledger de uso;
6. el usuario recibe una URL firmada de vida corta o una entrega autorizada; el pod se detiene al terminar o quedar idle.

Una foto adjunta por un usuario, una referencia oficial de una Queen, un derivado generado y una entrega compartida son objetos distintos. Cada uno necesita dueño, consentimiento, scope, retención y procedencia. Una Queen no decide URLs, permisos, herramientas ni acceso a otras conversaciones.

## Guardrails de implementación

- no usar originales privados ni personas reales en fixtures;
- no sobrescribir masters: trabajar con previews y derivados verificables;
- mantener prompts, scopes, consentimientos, entitlements y límites del lado servidor;
- escanear tipo, tamaño, malware, contenido y metadata antes de procesar o entregar;
- separar input del usuario, grounding oficial, output y exportación;
- apagar GPU y revocar URLs al finalizar; registrar costo estimado y real;
- no mostrar proveedor, workflow, credenciales o infraestructura a la Queen ni al usuario;
- aplicar retención y borrado verificables antes de vender la capacidad;
- no comprar, desplegar ni dejar un pod corriendo sin proveedor, presupuesto, alertas y aprobación del owner.

## Trabajo pendiente

**VERIFICADO:** la propuesta visualiza un workflow de referencia-preservación con ComfyUI y GPU bajo demanda; el VPS actual no tiene GPU, el producto ya separa objetivo multimodal, storage y autorización, y Flow/Mage son fuentes canónicas del owner con material existente.

**VERIFICADO POR EL OWNER:** Flow y Mage son ecosistemas canónicos, cubiertos por suscripciones con generación amplia y con material ya producido en masa. **INFERENCIA:** Cloud Lab es más valioso inicialmente como laboratorio/fallback/control propio que como motor económico principal de cada selfie; no debe usarse el PDF viejo para proyectar costos actuales.

**PENDIENTE:** medir límites, calidad, latencia, retención y términos de Flow/Mage; definir cuándo conviene el fallback Cloud Lab; sólo entonces comparar RunPod o Vast, presupuesto, storage privado, consentimiento, política de imágenes, colas/cancelación, workflow reproducible y calidad de identidad.

La autoridad funcional sigue siendo `SPECT.md`; la decisión concreta y sus consecuencias están en [`docs/adr/0007-payg-cloud-lab-and-tiered-media.md`](adr/0007-payg-cloud-lab-and-tiered-media.md). Esta hoja explica la implementación prevista, no eleva una propuesta a capacidad pública.
