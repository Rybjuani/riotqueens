"""Queen registry — Bardera loads the full /DOSSIER_MAESTRO.md (Owner 2026-08-28)."""

from __future__ import annotations

import os
import pathlib


# Legacy env name kept for compatibility; value must point at DOSSIER_MAESTRO.md.
_DOSSIER_ENV = "RIOTQUEENS_BARDERA_PRESET"
_DOSSIER_ENV_ALT = "RIOTQUEENS_DOSSIER_MAESTRO"


def _dossier_candidates() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for key in (_DOSSIER_ENV_ALT, _DOSSIER_ENV):
        env = os.environ.get(key, "").strip()
        if env:
            paths.append(pathlib.Path(env))
    paths.append(pathlib.Path("/app/DOSSIER_MAESTRO.md"))
    here = pathlib.Path(__file__).resolve()
    if len(here.parents) >= 5:
        paths.append(here.parents[4] / "DOSSIER_MAESTRO.md")
    paths.append(pathlib.Path("DOSSIER_MAESTRO.md"))
    paths.append(pathlib.Path("../../DOSSIER_MAESTRO.md"))
    return paths


def _load_bardera_dossier() -> str:
    for path in _dossier_candidates():
        try:
            if path.is_file():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    return text
        except OSError:
            continue
    raise FileNotFoundError(
        "DOSSIER_MAESTRO.md missing — full Bardera persona dossier required"
    )


BARDERA_SYSTEM_PROMPT = _load_bardera_dossier()

_QUEEN_SYSTEM_PROMPTS: dict[str, str] = {
    "bardera": BARDERA_SYSTEM_PROMPT,
}


def is_registered_queen(character_id: str) -> bool:
    return character_id in _QUEEN_SYSTEM_PROMPTS


def get_system_prompt(character_id: str) -> str | None:
    return _QUEEN_SYSTEM_PROMPTS.get(character_id)
