# Procedencia de assets web

Los archivos de esta tabla son copias de trabajo. Los originales externos al repo no fueron modificados.

La allowlist ejecutable está en [`../config/public-media.json`](../config/public-media.json). CI comprueba que las rutas y hashes coincidan y que ninguna entrada pública esté marcada como premium.

## Criterio de selección (owner)

El producto prioriza **compañeras conversacionales** (humor, creatividad, chat) con fotos de **presencia e identidad**, no un catálogo spicy. Las previews públicas deben leerse como “ella está ahí / en su mundo”.

Cada Queen mantiene **memoria y conversación aisladas** en backend por `character_id`. Las grillas del roster son previews provisionales: el owner reordena al verlas en pantalla.

Los masters seleccionados están ahora dentro del único workspace, en
`assets/private/selected/`, una ruta gitignored que no se sirve desde el VPS.
La copia fue verificada byte a byte contra el pool original: 66 archivos,
distribuidos entre Bardera (7), Chela (21), Gede (19), Rocha (2), Tóxica
Consciente (13) y cuatro piezas de moodboard/raíz. Flow y Mage son
ecosistemas canónicos externos del owner y contienen material ya producido;
sus assets sólo se vuelven parte del producto mediante una copia/derivado con
procedencia y hash.

La relación actual es explícita: los previews tracked en
`apps/web/public/queens/` son derivados públicos allowlisted del proceso de
curaduría y están hasheados en `config/public-media.json`; no hubo
coincidencia SHA-256 exacta con los 22 previews públicos, por lo que no se
afirma una relación master→slot individual todavía. Esa relación queda
`PENDING_OWNER_CURATED_MAPPING`, no se inventa por nombre de archivo.

**Evidencia recuperada:** la sesión que creó el roster dejó el índice
estructurado y los hashes, posteriormente incorporados en el commit
`093bc32`: 23 entradas allowlisted (logo + 22 previews: Bardera 5,
Tóxica 5, Gede 5, Rocha 2 y Chela 5). El estado verificable es
`config/public-media.json` junto con esta tabla; no corresponde recatalogar
esos previews desde cero. La selección final de masters/derivados sigue
siendo del owner.

## Brand

| Ruta web | Estado | Fuente | SHA-256 |
|---|---|---|---|
| `apps/web/public/brand/riotqueens-logo.jpeg` | `CANON / LOCKED` | logo oficial | `e47df47761cdee8da0b7674b0bdb8f35a71086c24474a33d2b496de67ad3e3b1` |

## Previews por Queen (provisional)

Rutas bajo `apps/web/public/queens/<id>/0N.jpg`. Hashes exactos en `config/public-media.json`.

| Queen | Slots | Runtime chat | Notas |
|---|---|---|---|
| `bardera` | 5 | **live** | 01–03 presencia/chat preferidas; 04–05 relleno provisional del pool de 7; reemplazo sólo mediante selección registrada desde fuentes canónicas |
| `toxica` | 5 | curación | presencia en cuarto |
| `gede` | 5 | curación | cuarto + retrato vertical |
| `rocha` | 2 | curación | pool chico; faltan 2–3 tomas |
| `chela` | 5 | curación | retrato + cuarto + escalera |

Sustituir un slot: reemplazar el archivo, actualizar hash en `public-media.json` y esta nota, y reordenar en `apps/web/lib/queen.ts` si cambia el rol.
