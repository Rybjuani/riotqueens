"""Fail closed when unregistered or premium media enters the public web tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.domain.contracts import MediaIntent, MediaType

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_ROOT = REPOSITORY_ROOT / "apps" / "web" / "public"
POLICY_PATH = REPOSITORY_ROOT / "config" / "public-media.json"
FORBIDDEN_SEGMENTS = {"master", "masters", "original", "originals", "premium", "private"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_every_public_media_file_is_nonpremium_allowlisted_and_unchanged() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    entries = {entry["path"]: entry for entry in policy["assets"]}
    actual_paths = {
        path.relative_to(PUBLIC_ROOT).as_posix()
        for path in PUBLIC_ROOT.rglob("*")
        if path.is_file()
    }

    assert actual_paths == set(entries), "Public media must be explicitly allowlisted."

    for relative_path, entry in entries.items():
        assert entry["premium"] is False, "Premium media must never enter public/."
        path_segments = {segment.lower() for segment in Path(relative_path).parts}
        assert not (path_segments & FORBIDDEN_SEGMENTS)
        assert _sha256(PUBLIC_ROOT / relative_path) == entry["sha256"]


def test_media_intent_contains_semantics_but_no_delivery_authority() -> None:
    intent = MediaIntent(
        user_id="user-1",
        character_id="bardera",
        conversation_id="conversation-1",
        media_type=MediaType.SELFIE,
        mood="casual_confident",
        context="conversation_reply",
    )

    assert intent.media_type is MediaType.SELFIE
    assert not hasattr(intent, "url")
    assert not hasattr(intent, "asset_id")


def test_media_intent_rejects_client_delivery_fields() -> None:
    with pytest.raises(ValueError):
        MediaIntent(
            user_id="user-1",
            character_id="bardera",
            conversation_id="conversation-1",
            media_type="selfie",
            url="https://example.invalid/private.jpg",
        )
