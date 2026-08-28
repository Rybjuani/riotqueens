# RIOTQUEENS_BIGPICKLE.md — v1.2

**Estado:** `RATIFICADO POR EL OWNER`  
**Orquestación:** Juani (Owner) + Qwen (Compi/Ordenador). Codex pica código, no decide. Big Pickle audita/documenta.  
**Nota:** Meta fuera tras el intento fallido del 08-26 (mezcló chiste con canon); su residuo útil queda rescatado en esta v1.2.

### §0. AUTORIDAD Y MENTES
- `AGENTS.md` manda. `BIGPICKLE` es la verdad del repo.
- Codex ejecuta cortes, **no decide**. Si duda: no inventa, escala al Owner.

### §1. REALIDAD ECONÓMICA
- **Presupuesto:** USD 5 / $40k ARS.
- **VPS:** OVH `148.113.167.121` (pago 1 mes).
- **LLM Backup:** GPT dado de baja (quedan ~15 días + 2 ventanas Codex: 1 normal + 1 reset gratis). Grok 1 semana como backup (`grok-cli` si Codex se queda sin crédito).
- **Regla de oro:** **NO se prende GPU hasta tener tope de gasto definido.**

### §2. ORDEN MACHETE (Anti-TDAH)
1. **Cerrar Vast.ai + Auth0** (pendiente = manija = burn).
2. **Lo otro:** Migración y ajustes menores.
3. **Pulir HTML + subir assets** que ya están.
- *Dinámica:* Juani = primer cliente, root gratis, tests exhaustivos. Lo hard va de a poco, **nunca todo de golpe**.

### §3. MODELOS Y TIERS
- **T1 (Preview):** `sao10k/l3.3-euryale-70b` vía OpenRouter (gratis/barato, límite diario).  
  *Caps OBLIGATORIAS:* `max_tokens` 180-220, `temp` 0.85-0.95. Roleplay no es megaplan. SAPE no es firma (cooldown 15 mensajes). Ban de genéricos.
- **T2 (Intermedio):** Modelo más barato que el 27B, multimodal. Selfies a demanda pagas. Assets = fotos/video 2K fotorealista editorial semi-sensual de Labs.Flow. Recibe foto del user.
- **T3 (Aspiracional):** `orcarouter/Qwen3.8-27B-Uncensored-FP8` en Vast.ai RTX 4090 spot (P1 cerrado BP-0001). Memoria larga + internet. **GPU gated por Owner.**

### §4. BARDERA: RETENCIÓN Y CANON
- **Derogado:** "Bardera te quiere" en landing/dossier careta.
- **Canónico:** "Te quiero" 1 vez en la vida, recurso escaso. T1 seduce y retiene sin regalarlo. Bardea con cariño: *"quedate, contame, bobo, yo te enseño, te banco los trapos"*.
- **Slogan oficial:** *"Tu anti perfect girlfriend que te banca en todas, no como las del Tinder que te hacen pagar Kansas y Uber y después te bloquean"*.
- **Manejo de pedidos explícitos:** **NO bloquear**. Redirigir al tier: *"Yo no soy de esas, pero la de T2/T3 por ahí acepta ese mambo"*.
- **Regla:** Nunca nombrar el modelo técnico. Lenguaje humanizado: son minas posta.

### §5. TRIBU Y CANON VISUAL
- **Roster:** **6 Riots**, no 5. La 6ª es trans, tier última (demanda por curiosidad).
- **Gestión:** Las Riots viven en NotebookLM con técnica del Owner (dossier + material visual para profiles).
- **Estética:** Canon SHEIN (lo último, atrevido pero legal). 
- **Anti candy.ai:** No IA prosti ni cabaret. Personalidad artesanal con alma. Sin upskirt. Contracultural pero sutil, siempre dentro del marco legal.

### §6. REPO CLEAN (NO HEREDAR BASURA)
- **Estrategia:** `RiotQueens-clean` nuevo. Worktree viejo solo como referencia de lectura.
- **Estructura:** 
  - `/apps` (FastAPI + `openai_compatible` capada).
  - `/web` (Landing 10 puntos + chat).
  - `/docs` (`AUTHORITY.md` única autoridad, `ROADMAP.md` único = el del Pickle, `MIGRATION.md`).
  - Raíz: `README` (mapa de 30 líneas), `docker-compose`, `.env.example`, `.gitignore`.
- **Limpieza:** Nombre raro → trash. Sin `node_modules` / `.venv` / `pycache` / `.git` / tarballs.
- **Prompt:** SKILLS de programación del experimento **NO** van al preset. Bardera: preset único de 80 líneas (`prompts/bardera.preset.md`). Los PDFs (`MANIFIESTO_BARDI`, `Evangelio de los Rotos`) van a `docs/canon/` como assets visuales, **NO al prompt**. `DossierBardera.md` queda como referencia humana.

### §7. PARA CODEX (CERRADO)
- Ejecuta cortes de `MIGRATION`, no decide.
- SSH key por path (`~/.ssh/luxriot_vps`), **nunca** en `.env`.
- `runtime.env` con permisos `600` por `scp`, **nunca** por Git.
- Verificación: `rg -i gemini` debe dar vacío.
- Push recién en Corte 6, tras auditoría.
- **Si duda: no inventa, escala al Owner.**