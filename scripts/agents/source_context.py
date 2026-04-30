"""
Source Context Agent for Batch 2.

This module gathers grounded planning records for a scene without filling
missing data or inventing values. Downstream agents receive the raw records
plus explicit missing-record and unresolved-marker warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


UNRESOLVED_RE = re.compile(r"\b(UNRESOLVED|TODO_REVIEW|TODO|EVIDENCE_THIN)\b")


@dataclass(frozen=True)
class SourceContext:
    """Verbatim source package for one scene."""

    scene_id: str
    scene_card: dict[str, Any]
    scene_excerpt: str | None
    characters: dict[str, dict[str, Any]]
    location: dict[str, Any] | None
    props: dict[str, dict[str, Any]]
    wardrobe: dict[str, dict[str, Any]]
    style_bible_text: str | None
    unresolved_warnings: list[str] = field(default_factory=list)
    missing_records: list[str] = field(default_factory=list)
    escalate: bool = False


def _read_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _collect_unresolved_markers(value: Any, root: str) -> list[str]:
    markers: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_root = f"{root}.{key}" if root else str(key)
            markers.extend(_collect_unresolved_markers(child, child_root))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            markers.extend(_collect_unresolved_markers(child, f"{root}[{index}]"))
    elif isinstance(value, str) and UNRESOLVED_RE.search(value):
        markers.append(f"{root}: {value[:160]}")
    return markers


def _append_markers(
    warnings: list[str],
    data: Any,
    root: str,
) -> None:
    for marker in _collect_unresolved_markers(data, root):
        warnings.append(f"UNRESOLVED marker in {marker}")


class SourceContextAgent:
    """Load scene-grounded planning records for downstream prompt agents."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def build(self, scene_id: str) -> SourceContext:
        warnings: list[str] = []
        missing: list[str] = []
        escalate = False

        scene_dir = self.repo_root / "planning" / "scenes" / scene_id
        scene_card_path = scene_dir / "scene_card.yaml"
        scene_card = _read_yaml(scene_card_path)
        if scene_card is None:
            missing.append(f"scene_card: {scene_card_path} not found or unreadable")
            warnings.append(f"ESCALATE: scene_card missing for {scene_id}")
            return SourceContext(
                scene_id=scene_id,
                scene_card={},
                scene_excerpt=None,
                characters={},
                location=None,
                props={},
                wardrobe={},
                style_bible_text=None,
                unresolved_warnings=warnings,
                missing_records=missing,
                escalate=True,
            )

        _append_markers(warnings, scene_card, "scene_card")

        excerpt_ref = str(scene_card.get("excerpt_ref") or "scene_excerpt.md")
        scene_excerpt_path = scene_dir / excerpt_ref
        scene_excerpt = _read_text(scene_excerpt_path)
        if scene_excerpt is None:
            missing.append(f"scene_excerpt: {scene_excerpt_path} not found")
        elif UNRESOLVED_RE.search(scene_excerpt):
            warnings.append(f"UNRESOLVED marker in scene_excerpt: {scene_excerpt_path}")

        characters: dict[str, dict[str, Any]] = {}
        for char_id in scene_card.get("characters_present", []) or []:
            char_path = self.repo_root / "planning" / "characters" / f"{char_id}.yaml"
            char_data = _read_yaml(char_path)
            if char_data is None:
                missing.append(f"character: {char_path} not found or unreadable")
                escalate = True
                continue
            characters[str(char_id)] = char_data
            _append_markers(warnings, char_data, f"character.{char_id}")

        location: dict[str, Any] | None = None
        loc_id = scene_card.get("location_id")
        if loc_id:
            loc_path = self.repo_root / "planning" / "locations" / f"{loc_id}.yaml"
            location = _read_yaml(loc_path)
            if location is None:
                missing.append(f"location: {loc_path} not found or unreadable")
                escalate = True
            else:
                _append_markers(warnings, location, f"location.{loc_id}")

        continuity_refs = scene_card.get("continuity_refs") or {}

        props: dict[str, dict[str, Any]] = {}
        for prop_id in continuity_refs.get("props", []) or []:
            prop_path = self.repo_root / "planning" / "props" / f"{prop_id}.yaml"
            prop_data = _read_yaml(prop_path)
            if prop_data is None:
                missing.append(f"prop: {prop_path} not found or unreadable")
                continue
            props[str(prop_id)] = prop_data
            _append_markers(warnings, prop_data, f"prop.{prop_id}")

        wardrobe: dict[str, dict[str, Any]] = {}
        for wardrobe_id in continuity_refs.get("wardrobe", []) or []:
            wardrobe_path = (
                self.repo_root / "planning" / "wardrobe" / f"{wardrobe_id}.yaml"
            )
            wardrobe_data = _read_yaml(wardrobe_path)
            if wardrobe_data is None:
                missing.append(f"wardrobe: {wardrobe_path} not found or unreadable")
                continue
            wardrobe[str(wardrobe_id)] = wardrobe_data
            _append_markers(warnings, wardrobe_data, f"wardrobe.{wardrobe_id}")

        style_bible_path = self.repo_root / "source" / "style_bible.md"
        style_bible_text = _read_text(style_bible_path)
        if style_bible_text is None:
            missing.append(f"style_bible: {style_bible_path} not found")
        elif UNRESOLVED_RE.search(style_bible_text):
            warnings.append(f"UNRESOLVED marker in style_bible: {style_bible_path}")

        return SourceContext(
            scene_id=scene_id,
            scene_card=scene_card,
            scene_excerpt=scene_excerpt,
            characters=characters,
            location=location,
            props=props,
            wardrobe=wardrobe,
            style_bible_text=style_bible_text,
            unresolved_warnings=warnings,
            missing_records=missing,
            escalate=escalate,
        )
