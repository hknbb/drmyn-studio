"""
tests/test_prop_continuity_state.py — Batch 1.5

Tests for prop continuity state resolution and schema normalization.
Verifies PROP001.yaml state_changes use scene_id (not 'transition').
All resolver tests use tmp_path — never read the real planning/ directory
(except the schema conformance test which validates real prop files).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Inline resolver (mirrors plan algorithm; moved to scripts/agents/continuity.py in Batch 2)
# ---------------------------------------------------------------------------

def resolve_prop_state_at_scene(prop_data: dict, target_scene_id: str) -> tuple[str, str | None]:
    """
    Resolve the continuity state of a prop at a given scene.

    Args:
        prop_data: Loaded prop YAML dict.
        target_scene_id: e.g. "SC0010"

    Returns:
        (resolved_state, warning_note) — warning_note is None if clean.
    """
    continuity = prop_data.get("continuity_state", {})
    resolved = continuity.get("initial_state", "")
    changes = sorted(
        continuity.get("state_changes", []),
        key=lambda c: int(c["scene_id"][2:])
    )
    target_num = int(target_scene_id[2:])
    for change in changes:
        if int(change["scene_id"][2:]) <= target_num:
            resolved = change["new_state"]
        else:
            break

    # Unresolved marker check
    if any(m in str(resolved) for m in ("UNRESOLVED", "TODO", "EVIDENCE_THIN")):
        return resolved, "WARNING: unresolved state — do not use in prompt"
    return resolved, None


# ---------------------------------------------------------------------------
# Fixtures — use tmp_path for all resolver tests
# ---------------------------------------------------------------------------

PROP001_DATA = {
    "prop_id": "PROP001",
    "name": "Jin's medical bracelet",
    "narrative_function": "Continuity-critical infant identifier.",
    "visual_description": "Thin hospital-style plastic bracelet.",
    "status": "review",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "White plastic hospital bracelet; Nadia listed as registrant. Worn by Jin in SC0003.",
        "state_changes": [
            {
                "scene_id": "SC0010",
                "transition_note": "Between SC0003 and SC0010 (exact scene not specified in source)",
                "new_state": (
                    "Pale blue band from a later check-up. SC0010 explicitly describes it as "
                    "'from his last check-up', indicating a replacement bracelet applied at a "
                    "more recent medical visit. This pale blue bracelet is the same object in "
                    "SC0011 and SC0014."
                ),
            }
        ],
    },
}

PROP_NO_CHANGES = {
    "prop_id": "PROP003",
    "name": "Tilted Vardova skyline photo frame",
    "narrative_function": "Intrusion cue.",
    "visual_description": "Framed landscape photograph.",
    "status": "review",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "Hanging slightly off-angle in the east-wing corridor.",
        "state_changes": [],
    },
}

PROP_UNRESOLVED = {
    "prop_id": "PROP_TEST",
    "name": "Test prop with unresolved state",
    "narrative_function": "Test only.",
    "visual_description": "Test.",
    "status": "draft",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "UNRESOLVED state from SC0001.",
        "state_changes": [],
    },
}


# ---------------------------------------------------------------------------
# Resolver tests — PROP001 (with state change at SC0010)
# ---------------------------------------------------------------------------


def test_prop001_before_change_returns_initial_state():
    """In SC0003 (before SC0010), state should be white plastic bracelet."""
    state, warning = resolve_prop_state_at_scene(PROP001_DATA, "SC0003")
    assert "white plastic" in state.lower() or "white" in state.lower()
    assert warning is None


def test_prop001_at_change_scene_returns_new_state():
    """In SC0010 (exactly at change), state should be pale blue band."""
    state, warning = resolve_prop_state_at_scene(PROP001_DATA, "SC0010")
    assert "pale blue" in state.lower()
    assert warning is None


def test_prop001_after_change_returns_new_state():
    """In SC0014 (after SC0010), state should still be pale blue band."""
    state, warning = resolve_prop_state_at_scene(PROP001_DATA, "SC0014")
    assert "pale blue" in state.lower()
    assert warning is None


def test_prop001_far_after_change_returns_last_known_state():
    """In SC0050 (no further state changes), still returns pale blue."""
    state, warning = resolve_prop_state_at_scene(PROP001_DATA, "SC0050")
    assert "pale blue" in state.lower()
    assert warning is None


# ---------------------------------------------------------------------------
# Resolver tests — prop with no state changes
# ---------------------------------------------------------------------------


def test_prop_no_changes_returns_initial_state():
    """A prop with empty state_changes always returns initial_state."""
    state, warning = resolve_prop_state_at_scene(PROP_NO_CHANGES, "SC0050")
    assert "off-angle" in state.lower() or "corridor" in state.lower()
    assert warning is None


# ---------------------------------------------------------------------------
# Resolver tests — unresolved state marker
# ---------------------------------------------------------------------------


def test_unresolved_state_returns_warning():
    """UNRESOLVED marker in state triggers a warning note."""
    state, warning = resolve_prop_state_at_scene(PROP_UNRESOLVED, "SC0001")
    assert warning is not None
    assert "WARNING" in warning
    assert "unresolved" in warning.lower()


# ---------------------------------------------------------------------------
# Schema conformance — real prop files pass updated prop_record.schema.json
# ---------------------------------------------------------------------------


def test_real_prop_files_pass_schema():
    """All planning/props/*.yaml files must pass prop_record.schema.json."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        pytest.skip("jsonschema not installed")

    schema_path = REPO_ROOT / "schemas" / "prop_record.schema.json"
    props_dir = REPO_ROOT / "planning" / "props"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    prop_files = list(props_dir.glob("*.yaml"))
    assert len(prop_files) > 0, "No prop files found in planning/props/"

    errors_found = []
    for prop_path in sorted(prop_files):
        data = yaml.safe_load(prop_path.read_text(encoding="utf-8"))
        file_errors = list(validator.iter_errors(data))
        for err in file_errors:
            field = ".".join(str(p) for p in err.absolute_path) or "(root)"
            errors_found.append(f"[{prop_path.name}] {field}: {err.message}")

    assert errors_found == [], "\n".join(errors_found)


# ---------------------------------------------------------------------------
# PROP001.yaml format check — no 'transition' key (renamed to transition_note)
# ---------------------------------------------------------------------------


def test_prop001_yaml_uses_scene_id_not_transition():
    """PROP001.yaml state_changes must use scene_id, not the deprecated 'transition' key."""
    prop_path = REPO_ROOT / "planning" / "props" / "PROP001.yaml"
    data = yaml.safe_load(prop_path.read_text(encoding="utf-8"))
    changes = data.get("continuity_state", {}).get("state_changes", [])
    assert len(changes) > 0, "PROP001 state_changes must not be empty"
    for change in changes:
        assert "scene_id" in change, f"state_changes entry missing scene_id: {change}"
        assert "transition" not in change, (
            f"state_changes entry still uses deprecated 'transition' key: {change}"
        )


def test_prop001_yaml_scene_id_is_sc0010():
    """PROP001.yaml state change must be at scene SC0010."""
    prop_path = REPO_ROOT / "planning" / "props" / "PROP001.yaml"
    data = yaml.safe_load(prop_path.read_text(encoding="utf-8"))
    changes = data.get("continuity_state", {}).get("state_changes", [])
    scene_ids = [c["scene_id"] for c in changes]
    assert "SC0010" in scene_ids, f"Expected SC0010 in state_changes, got: {scene_ids}"


# ---------------------------------------------------------------------------
# Validate phase1.py still passes after prop normalization
# ---------------------------------------------------------------------------


def test_validate_phase1_still_passes_after_prop_fix():
    """validate_phase1.py must exit 0 after prop_record.schema.json update."""
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_phase1.py"),
            "--source-dir", str(REPO_ROOT / "source"),
            "--planning-dir", str(REPO_ROOT / "planning"),
            "--prompts-dir", str(REPO_ROOT / "prompts"),
            "--schemas-dir", str(REPO_ROOT / "schemas"),
            "--evidence-dir", str(REPO_ROOT / "evidence"),
            "--report-json", str(REPO_ROOT / "evidence" / "validation_reports" / "phase1_validation_report.json"),
            "--report-md", str(REPO_ROOT / "evidence" / "validation_reports" / "phase1_validation_report.md"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_phase1.py failed after prop fix.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
