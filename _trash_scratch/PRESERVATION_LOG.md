# Log de preservación forense — 2026-08-28

Paso ejecutado: checklist §3 (preservación). Sin consolidación de Dossier, sin cambios de runtime/deploy/control-plane/memoria/max_tokens.

## Qué se preservó

1. **Variantes huérfanas VPS de `AGENTS.md`** → `_trash_scratch/legacy_vps_variants/`
2. **Tree dangling local `88ceac0…`** → `_trash_scratch/dangling_tree_88ceac0/`
3. **Inputs de consolidación** (snapshot) → `_trash_scratch/inputs_for_consolidation/`
4. **Inputs untracked** también versionados en la **raíz** del repo para la consolidación posterior.

## Qué NO se movió aún (sigue activo hasta pasos 4–6)

- `RIOTQUEENS_BIGPICKLE.md` (archivo original a archivar cuando exista `/AGENTS.md` de reemplazo)
- `docs/AUTHORITY.md` (gobernanza provisional hasta nuevo `AGENTS.md`)
- `prompts/bardera.preset.md` (runtime vigente; no tocar)
- `CLEAN-BARDERA-MARKDOWN.md` / `DossierBardera.md` en raíz (inputs activos; snapshot ya en trash)
