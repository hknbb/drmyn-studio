from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.continuity import (  # noqa: E402
    MissingPropRecordError,
    resolve_prop_state_at_scene,
)
from scripts.agents.source_context import SourceContextAgent  # noqa: E402


PROP001_DATA = {
    "prop_id": "PROP001",
    "name": "Jin's medical bracelet",
    "narrative_function": "Continuity-critical infant identifier.",
    "visual_description": "Thin hospital-style plastic bracelet.",
    "status": "review",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": (
            "White plastic hospital bracelet; Nadia listed as registrant. "
            "Worn by Jin in SC0003."
        ),
        "state_changes": [
            {
                "scene_id": "SC0010",
                "transition_note": "Between SC0003 and SC0010.",
                "new_state": (
                    "Pale blue band from a later check-up. This pale blue "
                    "bracelet is the same object in SC0011 and SC0014."
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
    "prop_id": "PROP999",
    "name": "Unresolved test prop",
    "narrative_function": "Test only.",
    "visual_description": "Test prop.",
    "status": "draft",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "TODO_REVIEW state from source pass.",
        "state_changes": [],
    },
}


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_continuity_repo(tmp_path: Path) -> Path:
    _write_yaml(tmp_path / "planning" / "props" / "PROP001.yaml", PROP001_DATA)
    _write_yaml(tmp_path / "planning" / "props" / "PROP003.yaml", PROP_NO_CHANGES)
    _write_yaml(tmp_path / "planning" / "props" / "PROP999.yaml", PROP_UNRESOLVED)
    return tmp_path


def test_prop001_resolves_white_before_sc0010(tmp_path: Path) -> None:
    repo = _make_continuity_repo(tmp_path)
    result = resolve_prop_state_at_scene(repo, "PROP001", "SC0003")
    assert "white plastic" in result.resolved_state.lower()
    assert result.note is None
    assert result.warning is None
    assert result.is_resolved is True


def test_prop001_resolves_pale_blue_at_and_after_sc0010(tmp_path: Path) -> None:
    repo = _make_continuity_repo(tmp_path)
    at_change = resolve_prop_state_at_scene(repo, "PROP001", "SC0010")
    after_change = resolve_prop_state_at_scene(repo, "PROP001", "SC0014")
    assert "pale blue" in at_change.resolved_state.lower()
    assert "pale blue" in after_change.resolved_state.lower()
    assert at_change.is_resolved is True
    assert after_change.is_resolved is True


def test_prop_without_state_changes_returns_initial_state(tmp_path: Path) -> None:
    repo = _make_continuity_repo(tmp_path)
    result = resolve_prop_state_at_scene(repo, "PROP003", "SC0050")
    assert "off-angle" in result.resolved_state.lower()
    assert result.warning is None
    assert result.is_resolved is True


def test_unresolved_marker_returns_warning(tmp_path: Path) -> None:
    repo = _make_continuity_repo(tmp_path)
    result = resolve_prop_state_at_scene(repo, "PROP999", "SC0001")
    assert result.is_resolved is False
    assert result.warning is not None
    assert "unresolved" in result.warning.lower()
    assert "TODO_REVIEW" in result.resolved_state


def test_props_state_overlay_adds_note_without_overriding_state(tmp_path: Path) -> None:
    repo = _make_continuity_repo(tmp_path)
    _write_yaml(
        repo / "planning" / "continuity" / "props_state.yaml",
        {
            "record_type": "props_state",
            "entries": [
                {
                    "scene_id": "SC0010",
                    "prop_id": "PROP001",
                    "state": "manual ledger note",
                    "notes": "operator should check clasp visibility",
                }
            ],
        },
    )

    result = resolve_prop_state_at_scene(repo, "PROP001", "SC0010")
    assert "pale blue" in result.resolved_state.lower()
    assert result.note is not None
    assert "manual ledger note" in result.note
    assert "clasp visibility" in result.note
    assert result.overlay_path is not None


def test_missing_prop_raises_explicit_failure(tmp_path: Path) -> None:
    with pytest.raises(MissingPropRecordError):
        resolve_prop_state_at_scene(tmp_path, "PROP404", "SC0001")


def test_source_context_loads_real_sc0003_grounding_package() -> None:
    context = SourceContextAgent(REPO_ROOT).build("SC0003")

    assert context.escalate is False
    assert context.scene_card["scene_id"] == "SC0003"
    assert context.scene_excerpt is not None
    assert "C01" in context.characters
    assert context.location is not None
    assert context.location.get("location_id") == "LOC001"
    assert "PROP001" in context.props
    assert "WD001" in context.wardrobe
    assert context.style_bible_text is not None


def test_source_context_missing_scene_card_escalates(tmp_path: Path) -> None:
    context = SourceContextAgent(tmp_path).build("SC9999")
    assert context.escalate is True
    assert context.scene_card == {}
    assert any("scene_card" in item for item in context.missing_records)


def test_source_context_missing_optional_prop_and_wardrobe_do_not_escalate(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path / "planning" / "scenes" / "SC0001" / "scene_card.yaml",
        {
            "scene_id": "SC0001",
            "location_id": "LOC001",
            "characters_present": ["C01"],
            "continuity_refs": {
                "wardrobe": ["WD999"],
                "props": ["PROP999"],
            },
            "excerpt_ref": "scene_excerpt.md",
        },
    )
    _write_text(
        tmp_path / "planning" / "scenes" / "SC0001" / "scene_excerpt.md",
        "A grounded scene excerpt.",
    )
    _write_yaml(
        tmp_path / "planning" / "characters" / "C01.yaml",
        {"character_id": "C01", "name": "Nadia"},
    )
    _write_yaml(
        tmp_path / "planning" / "locations" / "LOC001.yaml",
        {"location_id": "LOC001", "name": "Vale Residence"},
    )
    _write_text(tmp_path / "source" / "style_bible.md", "Quiet observational style.")

    context = SourceContextAgent(tmp_path).build("SC0001")
    assert context.escalate is False
    assert any("prop:" in item for item in context.missing_records)
    assert any("wardrobe:" in item for item in context.missing_records)


def test_source_context_carries_unresolved_markers_as_warnings(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "planning" / "scenes" / "SC0001" / "scene_card.yaml",
        {
            "scene_id": "SC0001",
            "purpose": "TODO_REVIEW: keep this unresolved for test.",
            "location_id": "LOC001",
            "characters_present": ["C01"],
            "continuity_refs": {"wardrobe": [], "props": []},
        },
    )
    _write_yaml(
        tmp_path / "planning" / "characters" / "C01.yaml",
        {"character_id": "C01", "name": "Nadia"},
    )
    _write_yaml(
        tmp_path / "planning" / "locations" / "LOC001.yaml",
        {"location_id": "LOC001", "name": "Vale Residence"},
    )
    _write_text(
        tmp_path / "planning" / "scenes" / "SC0001" / "scene_excerpt.md",
        dedent(
            """
            Nadia pauses.
            EVIDENCE_THIN: source line needs confirmation.
            """
        ).strip(),
    )
    _write_text(tmp_path / "source" / "style_bible.md", "Style text.")

    context = SourceContextAgent(tmp_path).build("SC0001")
    warnings = "\n".join(context.unresolved_warnings)
    assert "TODO_REVIEW" in warnings
    assert "scene_excerpt" in warnings
