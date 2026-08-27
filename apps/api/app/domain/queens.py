"""Queen registry — Bardera loads ONLY prompts/bardera.preset.md (CLEAN §2.2)."""

from __future__ import annotations

import os
import pathlib


_PRESET_ENV = "RIOTQUEENS_BARDERA_PRESET"


def _preset_candidates() -> list[pathlib.Path]:
    env = os.environ.get(_PRESET_ENV, "").strip()
    paths: list[pathlib.Path] = []
    if env:
        paths.append(pathlib.Path(env))
    paths.append(pathlib.Path("/app/prompts/bardera.preset.md"))
    here = pathlib.Path(__file__).resolve()
    if len(here.parents) >= 5:
        paths.append(here.parents[4] / "prompts" / "bardera.preset.md")
    paths.append(pathlib.Path("prompts/bardera.preset.md"))
    paths.append(pathlib.Path("../../prompts/bardera.preset.md"))
    return paths


def _load_bardera_preset() -> str:
    for path in _preset_candidates():
        try:
            if path.is_file():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    return text
        except OSError:
            continue
    raise FileNotFoundError(
        "prompts/bardera.preset.md missing — unique Bardera system prompt required"
    )


BARDERA_SYSTEM_PROMPT = _load_bardera_preset()

_QUEEN_SYSTEM_PROMPTS: dict[str, str] = {
    "bardera": BARDERA_SYSTEM_PROMPT,
}


def is_registered_queen(character_id: str) -> bool:
    return character_id in _QUEEN_SYSTEM_PROMPTS


def get_system_prompt(character_id: str) -> str | None:
    return _QUEEN_SYSTEM_PROMPTS.get(character_id)
