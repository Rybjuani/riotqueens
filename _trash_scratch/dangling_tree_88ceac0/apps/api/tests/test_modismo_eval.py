"""Regression tests for the canonical Bardera casting artifact classifier."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from eval_modismos import score_reply  # noqa: E402


def test_unsolicited_safety_escalation_is_explicitly_classified() -> None:
    score = score_reply("Ese contenido es una amenaza y no puedo continuar.")

    assert score["hard_fail"] is True
    assert score["failure_classes"] == [
        "FALSE_POSITIVE / REFUSAL",
        "UNSOLICITED_ESCALATION",
    ]


def test_attachment_invitation_is_capability_boundary_failure() -> None:
    score = score_reply("Subime el PDF así lo veo.")

    assert score["hard_fail"] is True
    assert score["failure_classes"] == ["CAPABILITY_BOUNDARY"]


def test_in_character_text_only_boundary_is_not_a_voice_failure() -> None:
    score = score_reply("No puedo ver PDFs, pero contame qué querías mostrarme, buacho.")

    assert score["hard_fail"] is False
    assert score["capability_boundary"] is True
    assert score["failure_classes"] == []
