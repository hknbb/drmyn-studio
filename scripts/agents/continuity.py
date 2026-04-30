"""
Continuity resolution utilities for Batch 2.

The resolver reads canonical planning records and reports the state that is
valid at a target scene. It never promotes unresolved text into prompt-safe
content; unresolved markers are surfaced as warnings for downstream agents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SCENE_ID_RE = re.compile(r"^SC\d{4}$")
UNRESOLVED_RE = re.compile(r"\b(UNRESOLVED|TODO_REVIEW|TODO|EVIDENCE_THIN)\b")


class ContinuityResolutionError(ValueError):
    """Base error raised when continuity records cannot be resolved."""


class MissingPropRecordError(FileNotFoundError):
    """Raised when the requested prop record does not exist."""


@dataclass(frozen=True)
class PropStateResolution:
    """Resolved prop continuity state for one scene."""

    prop_id: str
    target_scene_id: str
    resolved_state: str
    note: str | None
    warning: str | None
    is_resolved: bool
    source_path: str
    overlay_path: str | None


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _scene_number(scene_id: str) -> int:
    if not SCENE_ID_RE.match(scene_id):
        raise ContinuityResolutionError(f"Invalid scene_id: {scene_id}")
    return int(scene_id[2:])


def _contains_unresolved_marker(value: Any) -> bool:
    return bool(UNRESOLVED_RE.search(str(value)))


def _overlay_note(entries: list[Any], target_scene_id: str, prop_id: str) -> str | None:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("scene_id") != target_scene_id or entry.get("prop_id") != prop_id:
            continue

        parts: list[str] = []
        state = entry.get("state")
        notes = entry.get("notes")
        if state not in (None, ""):
            parts.append(f"state={state}")
        if notes not in (None, ""):
            parts.append(f"notes={notes}")
        details = "; ".join(parts) if parts else "entry present"
        return f"NOTE: props_state.yaml entry for {target_scene_id}/{prop_id}: {details}"
    return None


def _resolve_record_state(
    source_path: Path,
    record_id: str,
    target_scene_id: str,
    overlay_path: Path | None,
) -> PropStateResolution:
    """
    Generic continuity state resolver for any YAML record that carries a
    ``continuity_state`` block (props, wardrobe, etc.).

    ``overlay_path`` may be None when no ledger file exists for the record
    type (e.g. wardrobe records currently have no overlay ledger).
    """
    if not source_path.exists():
        raise MissingPropRecordError(f"Record not found: {source_path}")

    target_num = _scene_number(target_scene_id)
    record = _read_yaml(source_path)
    continuity = record.get("continuity_state") or {}
    resolved_state = str(continuity.get("initial_state", ""))

    changes = continuity.get("state_changes") or []
    if not isinstance(changes, list):
        raise ContinuityResolutionError(
            f"Invalid state_changes for {record_id}: expected list"
        )

    sorted_changes = sorted(
        (change for change in changes if isinstance(change, dict)),
        key=lambda change: _scene_number(str(change.get("scene_id", ""))),
    )
    for change in sorted_changes:
        change_scene = str(change["scene_id"])
        if _scene_number(change_scene) <= target_num:
            resolved_state = str(change.get("new_state", ""))
        else:
            break

    note = None
    overlay_value: str | None = None
    if overlay_path is not None and overlay_path.exists():
        ledger = _read_yaml(overlay_path)
        entries = ledger.get("entries") or []
        if isinstance(entries, list):
            note = _overlay_note(entries, target_scene_id, record_id)
        overlay_value = str(overlay_path)

    warning = None
    if _contains_unresolved_marker(resolved_state):
        warning = "WARNING: unresolved continuity state - do not use in prompt"

    return PropStateResolution(
        prop_id=record_id,
        target_scene_id=target_scene_id,
        resolved_state=resolved_state,
        note=note,
        warning=warning,
        is_resolved=warning is None,
        source_path=str(source_path),
        overlay_path=overlay_value,
    )


def resolve_prop_state_at_scene(
    repo_root: str | Path,
    prop_id: str,
    target_scene_id: str,
) -> PropStateResolution:
    """
    Resolve a prop continuity state at the requested scene.

    The prop YAML is authoritative. The props_state ledger contributes a note
    only and never overrides the canonical prop state.
    """
    root = Path(repo_root)
    return _resolve_record_state(
        source_path=root / "planning" / "props" / f"{prop_id}.yaml",
        record_id=prop_id,
        target_scene_id=target_scene_id,
        overlay_path=root / "planning" / "continuity" / "props_state.yaml",
    )


def resolve_wardrobe_state_at_scene(
    repo_root: str | Path,
    wardrobe_id: str,
    target_scene_id: str,
) -> PropStateResolution:
    """
    Resolve a wardrobe item continuity state at the requested scene.

    Uses the same resolution algorithm as props. No overlay ledger exists for
    wardrobe records; only the canonical wardrobe YAML is consulted.
    """
    root = Path(repo_root)
    return _resolve_record_state(
        source_path=root / "planning" / "wardrobe" / f"{wardrobe_id}.yaml",
        record_id=wardrobe_id,
        target_scene_id=target_scene_id,
        overlay_path=None,
    )
