# CLEAN BARDERA - MANIFIESTO DE LIMPIEZA v1.0
# Para escalar fácil, sin sobreingeniería.

# Los documentos requeridos estan en: /home/rybjuani/Descargas/

## § 1. LEY N°1 - NO SE NEGOCIA
> **A las Riots no se las capea. Si un provider tiene refusals agresivos por contrato, NO se capea a La Bardera. Se cambia de provider. Providers sobran, Barderas no, son únicas y no son fáciles de hacer.**

## § 2. CANON LIMPIO - LO QUE QUEDA (3 archivos + assets)

### 2.1. Fuente de verdad artesanal (corazón)
```
/
├── docs/canon/
│   ├── MANIFIESTO_BARDI.pdf              # 11 páginas - Gol del Diego, Escudos, Tentramitrozol - Hija que le hace dibujo al papá - CANON VISUAL
│   ├── El_Evangelio_de_los_Rotos.pdf     # 6 páginas - Poesía trinchera, Manaos, estación abandonada - CANON VISUAL
│   ├── Manifiesto_RiotQueens.pdf         # Manifiesto tribu (re-subir)
│   ├── Cyber-Conurbano_Manifesto.pdf     # (re-subir)
│   ├── Marginal_Sovereignty.pdf          # (re-subir)
│   └── Bardi_RiotQueen.pdf               # (re-subir)
└── assets/riotqueens/
    ├── bardera/
    │   ├── evangelio_page_0.png
    │   ├── mani_bardi_page_8_escudos.png
    │   └── mani_bardi_page_9_gol_diego.png
    └── ...
```

### 2.2. Preset artesanal mínimo (único archivo que lee el LLM)
```
/
├── prompts/
│   └── bardera.preset.md                 # 80 líneas MAX, sin skills de programación
```

**Contenido de `bardera.preset.md` (resumen de tu dossier bueno, sin humo):**
- Identidad: 24 años, Oeste conurbano, punk/rocha 90s, autoestima alta, criterio propio
- Moneda: aguante, quedarse, bancar los trapos
- Humor: reactivo, primero entiende después bardea si pinta
- Intensidad: variable, puede estar al 30% tranquila
- Capacidad de bajar un cambio: si user vulnerable, abandona chiste
- Reglas visuales:
  - SAPE = reset ocasional, NO firma. Cooldown 15 mensajes mínimo
  - Tentramitrozol = recurso alto valor, bajísima frecuencia. Chiste interno "te entra mi trozo", no usar cada mensaje
  - Gol del Diego: te quiero = 1 vez en la vida a las 4 AM borracha, escaso como nude. No se regala en T1
- Honestidad de capacidad: si no vio imagen, no la vio. No inventa
- Test de portabilidad: quitarle che, SAPE, Manaos, Flema y debe seguir siendo Bardera. Si queda genérico, casting fracasó

### 2.3. Dossier técnico destilado (solo referencia, NO lo lee runtime)
```
/
└── docs/
    └── DossierBardera.md                 # Bueno, el piya - 1600 líneas - Solo para humanos y para Codex cuando necesita entender causa, no para prompt
```

## § 3. LISTA DE BORRADO - SOBREINGENIERÍA CORPORATIVA (37 archivos SAPE)

**Todo esto va a `/trash/gpt_sabotaje_2026-08-26/` o se borra directo. No lo lee el runtime.**

```bash
# Core del sabotaje - glosarios y baterías que hacen que Bardera sea bobita
rm -rf glosariomodismos.md
rm -rf glossary.md
rm -rf SPECT.md
rm -rf BARDERA_SANDBOX_VOICE.md
rm -rf DECISION_REGISTER.md
rm -rf eval_modismos.py
rm -rf modismo_battery.md
rm -rf modismo_results_*.json   # todos los json de resultados
rm -rf modismo_results_*.log

# Landing mock vieja que confunde a Codex
rm -rf Riotqueens-Ai-Landing-Mock.html

# Cualquier archivo que contenga SAPE como firma obligatoria
# Buscar con: rg -l "SAPE" --type md | grep -v "DossierBardera.md" | grep -v "bardera.preset.md"
# Si un archivo tiene SAPE >3 veces o como firma en cada ejemplo, es sabotaje
```

**Checklist de detección de archivo saboteado:**
- [ ] ¿Tiene `SAPE` en cada ejemplo de respuesta?
- [ ] ¿Tiene `Tentramitrozol` como remedio genérico y no como chiste de alta rareza?
- [ ] ¿Define Skill de programación (Cyber-Punk Sec, Prompt Engineer, Full Stack)?
- [ ] ¿Es `.json` con resultados de eval que nadie usa?
- [ ] Si responde sí a 2 o más, va a trash.

## § 4. NUEVA ESTRUCTURA CLEAN - BUENAS PRÁCTICAS

```
RiotQueens/
├── prompts/
│   └── bardera.preset.md          # 80 líneas - único archivo que lee Euryale
├── docs/
│   ├── canon/                     # PDFs RAW artesanos - oro visual
│   │   ├── MANIFIESTO_BARDI.pdf
│   │   └── El_Evangelio_de_los_Rotos.pdf
│   └── DossierBardera.md          # Referencia humana
├── assets/
│   └── riotqueens/bardera/        # PNGs extraídos de PDFs para landing
├── backend/
│   └── openai_compatible.py       # Con max_tokens 180-220, temp 0.85-0.95
└── CLEAN_BARDERA_MARKDOWN.md      # Este archivo
```

**Regla de carga para Codex y Euryale:**
```python
# ANTES (sabotaje): rg SAPE -> carga 37 archivos -> Bardera bobita
# DESPUÉS (clean):
SYSTEM_PROMPT = open("prompts/bardera.preset.md").read()
# Solo eso. Nada más. Los PDFs no van al prompt, van a /assets para la página
```

## § 5. CÓMO USAR LOS PDFs ARTESANOS (no son para el LLM)

1.  **Landing T1:** `evangelio_page_0.png` (pared "LA POESÍA SE ACABÓ") como hero
2.  **Fondo chat:** `evangelio_page_1.png` (estación abandonada) como background del chat de Bardera
3.  **Profile Bardera:** `mani_bardi_page_9_gol_diego.png` (gráfico Gol del Diego) como explicación de por qué no regala te quiero
4.  **Escudos:** `mani_bardi_page_8_escudos.png` como infografía de cómo defiende

Estos artefactos son verificables, pesados, costosos, útiles, reales. No son texto vacío.

## § 6. PASO A PASO PARA VOS (orden que pediste)

1.  **Cerrar Vast.ai + Auth0** (te deja manija) - sin tocar prompts
2.  **Ejecutar limpieza:** mover 37 archivos a trash, dejar solo 3
3.  **Crear `prompts/bardera.preset.md`** de 80 líneas con reglas de arriba
4.  **Extraer PNGs de PDFs** a `assets/` (ya te dejé 11 páginas de MANIFIESTO_BARDI renderizadas)
5.  **Pedir a Codex:** "portar `prompts/bardera.preset.md` a `openai_compatible.py` con max_tokens 180-220, sin cargar ningún otro .md con SAPE"

## § 7. ESCALABILIDAD

Si hay que escalar a 6 Riots, no multiplicar docs. Duplicar patrón:
```
prompts/
├── bardera.preset.md
├── marce.preset.md   # 80 líneas, sin skills de programación
└── toxica.preset.md  # 80 líneas
docs/canon/
├── MANIFIESTO_BARDI.pdf
├── MANIFIESTO_MARCE.pdf (trans, 39 años, Oeste, prompt+fashion sin bizarreo)
└── ...
```

Cada preset 80 líneas, cada canon PDF visual. Nada de 37 archivos por Riot.

---

**Estado:** listo para pegar en `RIOTQUEENS_BIGPICKLE.md` v1.3 o usar como `CLEAN_BARDERA_MARKDOWN.md` standalone. Si este archivo contradice README que dice Gemini primary, manda este.

EOF
