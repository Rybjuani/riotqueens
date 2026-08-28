# Registro de fuentes de Queens y reciclaje creativo

**Autoridad:** registro de procedencia. `SPECT.md` gobierna el producto; este documento sólo clasifica evidencia y evita que una fuente se convierta accidentalmente en prompt o copy público.

## Fuentes auditadas

| Fuente | Clasificación | Uso permitido | SHA-256 |
|---|---|---|---|
| `docs/reference/audits/Qwen_html.html` (origen: `Escritorio/mix archivos/Qwen_html.html`) | VERIFICADO / referencia visual-estructural | rescatar composición, tokens, flujo y ADN; revalidar copy contra SPECT | `600c873eb5d9c40f5bb964c2aab4c61780a97e9886f1319ab1591b8a8a481b2a` |
| `Escritorio/barderainvernadero.png` | VERIFICADO / evidencia de flujo NotebookLM | documentar personalización y perfil; no servir | `2ced6d941a7d01c1780495b070b510b37330f416e904919859cc457c759ee52b` |
| `Escritorio/MANIFIESTO_BARDI.pdf` | CANON AUTORAL / fuente madre visual | derivar perfil estructurado; no usar como prompt literal | `4e947053f03c6d85bc01efaa03e00d490b36fe124502de5cd6461ed104df76e1` |
| `docs/canon/queens/bardera/glosariomodismos.md` (origen: `Escritorio/glosariomodismos.md`) | CANON AUTORAL / corpus de evaluación | benchmark y regresión; no copiar respuestas literales | `22d7e22a9c8779967e0b3ed4b8de7d9556131581c0d0935f53816f5123dd4b4f` |
| `Descargas/MANIFIESTO RIOTQUEEN DEL OESTE_ RITMO, SUSTANCIA Y AGUANTE.md` | CANON AUTORAL / manifiesto del owner | lore, identidad y vocabulario; claims públicos requieren revalidación | `564c7a8fb6d582c4d0a866cf03c7af12fdfbe79da735b4638480282d8993720f` |
| `Flow` | CANON VISUAL DEL OWNER / ecosistema externo | fuente primaria de material visual ya producido; cada asset requiere procedencia, Queen, versión y estado antes de importarse | fuera del repo; registrar hash al incorporar derivados |
| `Mage.space` | CANON VISUAL DEL OWNER / ecosistema externo | fuente primaria de material visual ya producido; cada asset requiere procedencia, Queen, versión y estado antes de importarse | fuera del repo; registrar hash al incorporar derivados |

## Propuesta externa de Cloud Lab

La propuesta de `/Escritorio/propuesta/` se conserva fuera del repo. Es evidencia de intención y diseño operativo, no una segunda autoridad. Su auditoría y clasificación están en [`docs/CLOUD_LAB.md`](../CLOUD_LAB.md); sus hashes permiten detectar cambios sin copiar PDFs, capturas ni workflows privados al producto.

## Material creativo incorporado al workspace

`assets/private/selected/` conserva los masters y selecciones del owner con
subcarpetas por Queen y la intención explícita de revisar 4–5 fotos en pantalla
y reordenarlas con coherencia de personalidad. Es privado y gitignored; no es
un segundo repo. Los archivos con branding no vigente o sin procedencia clara
son referencias de trabajo, no assets públicos automáticos.

Los previews actuales en `apps/web/public/` son copias provisionales ya registradas en `docs/ASSET_PROVENANCE.md` y `config/public-media.json`. No se sobrescriben masters; cada reemplazo exige hash, procedencia, estado premium y revisión del owner.

## Pendientes de procedencia

- exportar, si el owner lo autoriza, los informes del NotebookLM autenticado y registrar sus hashes;
- asociar cada imagen seleccionada a Queen, pose, derivado, estado y fuente original;
- completar glosarios y baterías independientes de Tóxica Consciente, Gede, Rocha y Chela;
- separar visualmente `referencia`, `preview pública` y `asset premium` antes de cualquier entrega de navegador.
