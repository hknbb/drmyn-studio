"""
aesthetic_bible.py

Loader and deterministic resolver for the DRMYN Studio Film Aesthetic Bible
(planning/aesthetic_bible.yaml). Provides named mood-board packs that scene
cards and element records reference via aesthetic_pack_refs, and a small
helper API that downstream agents (SourceContext, NeutralBrief, adapters)
can call in later batches.

This module is read-only and metadata-only: it never fetches from the
network, never writes to disk, and never promotes lifecycle state. All
helpers are deterministic given the same inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml


AESTHETIC_BIBLE_RELATIVE_PATH = Path("planning") / "aesthetic_bible.yaml"


class AestheticBibleError(Exception):
    """Raised when the aesthetic bible file is malformed at load time."""


@dataclass(frozen=True)
class AestheticPack:
    pack_id: str
    name: str
    visual_thesis: str
    derived_from: Mapping[str, Sequence[str]]
    search_keywords: tuple[str, ...]
    element_keyword_map: Mapping[str, tuple[str, ...]]
    do_not_keywords: tuple[str, ...]


@dataclass(frozen=True)
class AestheticBible:
    schema_version: int
    packs: tuple[AestheticPack, ...]

    def get_pack(self, pack_id: str) -> AestheticPack | None:
        for pack in self.packs:
            if pack.pack_id == pack_id:
                return pack
        return None


def load_aesthetic_bible(repo_root: Path) -> AestheticBible | None:
    """
    Load planning/aesthetic_bible.yaml from the given repo root.

    Returns None if the file does not exist. This is intentional: scenes
    that do not reference any pack must still build cleanly, and scenes
    in a repo without an aesthetic bible at all must not break.

    Raises AestheticBibleError if the file exists but is structurally
    malformed (e.g. not a mapping, missing required top-level keys).
    Schema-level validation is performed by validate_production_records.py
    via JSON Schema; this loader only enforces structural shape.
    """
    path = repo_root / AESTHETIC_BIBLE_RELATIVE_PATH
    if not path.is_file():
        return None

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise AestheticBibleError(
            f"{AESTHETIC_BIBLE_RELATIVE_PATH.as_posix()} must be a mapping."
        )

    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise AestheticBibleError(
            "schema_version must be 1; "
            f"got {schema_version!r}."
        )

    packs_raw = raw.get("packs")
    if not isinstance(packs_raw, list) or not packs_raw:
        raise AestheticBibleError("packs must be a non-empty list.")

    packs: list[AestheticPack] = []
    for index, pack_raw in enumerate(packs_raw):
        if not isinstance(pack_raw, dict):
            raise AestheticBibleError(f"packs[{index}] must be a mapping.")
        try:
            packs.append(_pack_from_raw(pack_raw))
        except AestheticBibleError as exc:
            raise AestheticBibleError(f"packs[{index}]: {exc}") from exc

    return AestheticBible(schema_version=1, packs=tuple(packs))


def _pack_from_raw(raw: Mapping[str, object]) -> AestheticPack:
    required = (
        "pack_id",
        "name",
        "visual_thesis",
        "derived_from",
        "search_keywords",
        "element_keyword_map",
        "do_not_keywords",
    )
    for key in required:
        if key not in raw:
            raise AestheticBibleError(f"required field {key!r} is missing.")

    derived_from_raw = raw["derived_from"]
    if not isinstance(derived_from_raw, dict):
        raise AestheticBibleError("derived_from must be a mapping.")
    derived_from: dict[str, tuple[str, ...]] = {}
    for key, value in derived_from_raw.items():
        if not isinstance(value, list):
            raise AestheticBibleError(f"derived_from.{key} must be a list.")
        derived_from[str(key)] = tuple(str(v) for v in value)

    search_keywords_raw = raw["search_keywords"]
    if not isinstance(search_keywords_raw, list):
        raise AestheticBibleError("search_keywords must be a list.")

    element_map_raw = raw["element_keyword_map"]
    if not isinstance(element_map_raw, dict):
        raise AestheticBibleError("element_keyword_map must be a mapping.")
    element_keyword_map: dict[str, tuple[str, ...]] = {}
    for key, value in element_map_raw.items():
        if not isinstance(value, list):
            raise AestheticBibleError(
                f"element_keyword_map.{key} must be a list."
            )
        element_keyword_map[str(key)] = tuple(str(v) for v in value)

    do_not_raw = raw["do_not_keywords"]
    if not isinstance(do_not_raw, list):
        raise AestheticBibleError("do_not_keywords must be a list.")

    return AestheticPack(
        pack_id=str(raw["pack_id"]),
        name=str(raw["name"]),
        visual_thesis=str(raw["visual_thesis"]),
        derived_from=derived_from,
        search_keywords=tuple(str(v) for v in search_keywords_raw),
        element_keyword_map=element_keyword_map,
        do_not_keywords=tuple(str(v) for v in do_not_raw),
    )


def _ordered_dedupe(values: Sequence[str]) -> list[str]:
    """Return values with duplicates removed, preserving first occurrence order."""
    return list(dict.fromkeys(values))


def get_pack_ids_from_records(
    scene_card: Mapping[str, object] | None,
    element_record: Mapping[str, object] | None = None,
) -> list[str]:
    """
    Deterministic ordered union of scene-level and element-level
    aesthetic_pack_refs.

    Scene refs come from scene_card['visual_targets']['aesthetic_pack_refs'].
    Element refs come from element_record['aesthetic_pack_refs'].
    Either source may be missing entirely; that is allowed.

    Order rule: scene refs first (in their declared order), then element
    refs (in their declared order), with duplicates removed. This is
    stable across runs given the same inputs.
    """
    refs: list[str] = []

    if isinstance(scene_card, Mapping):
        visual_targets = scene_card.get("visual_targets")
        if isinstance(visual_targets, Mapping):
            scene_refs = visual_targets.get("aesthetic_pack_refs")
            if isinstance(scene_refs, list):
                refs.extend(str(r) for r in scene_refs)

    if isinstance(element_record, Mapping):
        element_refs = element_record.get("aesthetic_pack_refs")
        if isinstance(element_refs, list):
            refs.extend(str(r) for r in element_refs)

    return _ordered_dedupe(refs)


def resolve_pack_keywords(
    packs: Sequence[AestheticPack],
    pack_ids: Sequence[str],
    prompt_type: str,
    limit_per_pack: int = 2,
) -> list[str]:
    """
    For each pack_id (in the order given), look up the pack and append the
    first ``limit_per_pack`` keywords from its element_keyword_map[prompt_type].
    Unknown pack_ids and pack_ids whose element_keyword_map does not contain
    prompt_type are silently skipped — the registry decides which prompt
    types it supports per pack.

    Returns the ordered, deduplicated list of keywords. Deterministic: the
    same inputs always produce the same output.
    """
    if limit_per_pack < 0:
        raise ValueError("limit_per_pack must be >= 0.")

    by_id = {pack.pack_id: pack for pack in packs}
    collected: list[str] = []
    for pack_id in pack_ids:
        pack = by_id.get(pack_id)
        if pack is None:
            continue
        bucket = pack.element_keyword_map.get(prompt_type)
        if not bucket:
            continue
        collected.extend(bucket[:limit_per_pack])

    return _ordered_dedupe(collected)


def resolve_pack_negatives(
    packs: Sequence[AestheticPack],
    pack_ids: Sequence[str],
) -> list[str]:
    """
    Ordered, deduplicated union of do_not_keywords across the requested
    packs. Unknown pack_ids are skipped. Deterministic.
    """
    by_id = {pack.pack_id: pack for pack in packs}
    collected: list[str] = []
    for pack_id in pack_ids:
        pack = by_id.get(pack_id)
        if pack is None:
            continue
        collected.extend(pack.do_not_keywords)

    return _ordered_dedupe(collected)
