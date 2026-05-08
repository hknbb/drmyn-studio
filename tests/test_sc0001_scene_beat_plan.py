"""
B4 tests: SC0001 scene_beat_plan.yaml validation and coverage.

Covers:
- Scene_beat_plan.yaml loads and is valid YAML.
- Record validates against schemas/scene_beat_plan.schema.json.
- Semantic validator (A3.1) returns no errors.
- No duration_seconds anywhere in the record.
- beat_id values are unique within scene.
- All dialogue content from source excerpt is covered by dialogue-role beats.
- Required narrative elements present (keywords: kitchen, scar, frame, Jin, etc.).
- No Kling-bound fields (clip_count, shots, total_duration_seconds, source_beat_ids).
- Beat count and semantic_duration_hint distribution match expectations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validators.validate_scene_beat_plan import (
    SceneBeatPlanValidationError,
    validate_scene_beat_plan,
)

SCENE_BEAT_PLAN_PATH = REPO_ROOT / "planning" / "scenes" / "SC0001" / "scene_beat_plan.yaml"
SCHEMA_PATH = REPO_ROOT / "schemas" / "scene_beat_plan.schema.json"


def _load_scene_beat_plan() -> dict:
    with SCENE_BEAT_PLAN_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# File and Structure Tests
# ---------------------------------------------------------------------------


def test_scene_beat_plan_file_exists() -> None:
    assert SCENE_BEAT_PLAN_PATH.exists(), f"Scene beat plan not found: {SCENE_BEAT_PLAN_PATH}"


def test_scene_beat_plan_is_valid_yaml() -> None:
    record = _load_scene_beat_plan()
    assert isinstance(record, dict), "Scene beat plan must be a YAML dictionary"
    assert record.get("record_type") == "scene_beat_plan"
    assert record.get("scene_id") == "SC0001"


def test_scene_beat_plan_schema_version() -> None:
    record = _load_scene_beat_plan()
    assert record.get("schema_version") == "0.x-draft"


def test_scene_beat_plan_has_source_beats_array() -> None:
    record = _load_scene_beat_plan()
    assert "source_beats" in record, "Record must have source_beats array"
    assert isinstance(record["source_beats"], list)
    assert len(record["source_beats"]) > 0, "source_beats must not be empty"


# ---------------------------------------------------------------------------
# JSON Schema Validation
# ---------------------------------------------------------------------------


def test_scene_beat_plan_validates_against_schema() -> None:
    schema = _load_schema()
    record = _load_scene_beat_plan()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(record))
    assert errors == [], f"Schema validation failed: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# Semantic Validation (A3.1)
# ---------------------------------------------------------------------------


def test_scene_beat_plan_semantic_validation_passes() -> None:
    record = _load_scene_beat_plan()
    errors = validate_scene_beat_plan(record)
    assert errors == [], f"Semantic validation failed: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# Duration Field Tests
# ---------------------------------------------------------------------------


def test_no_duration_seconds_at_scene_level() -> None:
    record = _load_scene_beat_plan()
    assert (
        "duration_seconds" not in record
    ), "scene_beat_plan must not have duration_seconds at scene level"


def test_no_duration_seconds_in_any_beat() -> None:
    record = _load_scene_beat_plan()
    for i, beat in enumerate(record["source_beats"]):
        assert (
            "duration_seconds" not in beat
        ), f"beat {i} ({beat.get('beat_id')}) must not have duration_seconds"


def test_no_duration_fields_anywhere() -> None:
    """Comprehensive check for any duration-related fields that shouldn't be present."""
    record = _load_scene_beat_plan()
    forbidden_fields = {
        "duration_seconds",
        "clip_count",
        "total_duration_seconds",
        "shot_duration",
        "duration_ms",
    }
    # Scene level
    found = set(record.keys()) & forbidden_fields
    assert not found, f"Scene level has forbidden duration fields: {found}"
    # Beat level
    for beat in record["source_beats"]:
        found = set(beat.keys()) & forbidden_fields
        assert not found, f"Beat {beat.get('beat_id')} has forbidden duration fields: {found}"


# ---------------------------------------------------------------------------
# beat_id Uniqueness
# ---------------------------------------------------------------------------


def test_beat_ids_are_unique() -> None:
    record = _load_scene_beat_plan()
    beat_ids = [beat["beat_id"] for beat in record["source_beats"]]
    assert len(beat_ids) == len(
        set(beat_ids)
    ), f"Duplicate beat_id found in SC0001: {[id for id in beat_ids if beat_ids.count(id) > 1]}"


def test_all_beat_ids_match_pattern() -> None:
    record = _load_scene_beat_plan()
    import re

    pattern = re.compile(r"^[A-Z0-9_]+$")
    for beat in record["source_beats"]:
        beat_id = beat["beat_id"]
        assert (
            pattern.match(beat_id)
        ), f"beat_id {beat_id!r} does not match pattern ^[A-Z0-9_]+$"


# ---------------------------------------------------------------------------
# Dialogue Content Coverage
# ---------------------------------------------------------------------------


def test_all_dialogue_lines_present() -> None:
    """Verify that all 8 dialogue lines from source excerpt are covered."""
    record = _load_scene_beat_plan()
    content_text = "\n".join(beat.get("content", "") for beat in record["source_beats"])

    # All 8 dialogue lines from source excerpt
    expected_lines = [
        "You didn't sleep again",
        "I slept",
        "You slept the way you fold laundry",
        "Jin's formula",
        "second shelf, behind the vitamin drops",
        "Mr. Vale called from the car",
        "not to wait on breakfast",
        "He won't be back before eight",
    ]

    for line in expected_lines:
        assert (
            line in content_text
        ), f"Dialogue line {line!r} not found in source_beats content"


def test_dialogue_beats_have_dialogue_role() -> None:
    record = _load_scene_beat_plan()
    dialogue_beat_ids = [
        "DIALOGUE_SLEEP_ACCUSATION",
        "DIALOGUE_FORMULA_VITAMIN",
        "DIALOGUE_MR_VALE_CALL",
        "NADIA_PRIOR_KNOWLEDGE",
        "BIRTA_COVERED_LINENS",
    ]
    for beat in record["source_beats"]:
        if beat["beat_id"] in dialogue_beat_ids:
            assert beat.get("narrative_role") == "dialogue", (
                f"Beat {beat['beat_id']} should have narrative_role='dialogue', "
                f"got {beat.get('narrative_role')!r}"
            )


# ---------------------------------------------------------------------------
# Narrative Content Coverage
# ---------------------------------------------------------------------------


def test_required_narrative_content_keywords() -> None:
    """Verify that required narrative elements are present via keyword search."""
    record = _load_scene_beat_plan()
    content_text = "\n".join(beat.get("content", "") for beat in record["source_beats"])
    notes_text = "\n".join(
        beat.get("notes", "") + (record.get("notes") or "") for beat in record["source_beats"]
    )
    full_text = (content_text + "\n" + notes_text).lower()

    required_elements = {
        "kitchen": "Kitchen environment",
        "expensive": "Expensive kitchen descriptor",
        "pale stone": "Pale stone surfaces",
        "cup": "Single unwashed cup",
        "wrist": "Wrist scar and pulse-check",
        "scar": "Wrist surgical scar",
        "cabinet": "Cabinet inventory action",
        "corridor": "East-wing corridor",
        "birta": "Birta character introduction",
        "formula": "Jin's formula (child care)",
        "vitamin": "Vitamin drops reference",
        "mr. vale": "Mr. Vale (husband)",
        "photograph": "Third framed photograph",
        "vardova": "Vardova skyline",
        "frame": "Frame straightening and dust-shadow",
        "dust": "Dust-shadow evidence",
        "jin": "Jin's room and crib observation",
        "crib": "Jin sleeping in crib",
        "inventory": "Inventory-like observation pattern",
    }

    for keyword, description in required_elements.items():
        assert (
            keyword in full_text
        ), f"Required element ({description}) not found; expected keyword {keyword!r}"


# ---------------------------------------------------------------------------
# Semantic Duration Hints Distribution
# ---------------------------------------------------------------------------


def test_semantic_duration_hints_valid() -> None:
    record = _load_scene_beat_plan()
    valid_hints = {"short_insert", "normal", "long_hold"}
    for beat in record["source_beats"]:
        hint = beat.get("semantic_duration_hint")
        assert (
            hint in valid_hints
        ), f"Beat {beat['beat_id']} has invalid semantic_duration_hint: {hint!r}"


def test_semantic_duration_distribution() -> None:
    record = _load_scene_beat_plan()
    hints = {}
    for beat in record["source_beats"]:
        hint = beat.get("semantic_duration_hint")
        hints[hint] = hints.get(hint, 0) + 1

    # Expect at least some normal and short_insert beats
    assert (
        hints.get("normal", 0) >= 10
    ), f"Expected at least 10 normal beats, got {hints.get('normal', 0)}"
    assert (
        hints.get("short_insert", 0) >= 4
    ), f"Expected at least 4 short_insert beats, got {hints.get('short_insert', 0)}"
    assert (
        hints.get("long_hold", 0) >= 1
    ), f"Expected at least 1 long_hold beat, got {hints.get('long_hold', 0)}"


# ---------------------------------------------------------------------------
# Narrative Role Distribution
# ---------------------------------------------------------------------------


def test_narrative_roles_valid() -> None:
    record = _load_scene_beat_plan()
    valid_roles = {
        "establish",
        "action",
        "dialogue",
        "hold",
        "transition",
        "pulse_check",
        "insert",
    }
    for beat in record["source_beats"]:
        if "narrative_role" in beat:
            role = beat["narrative_role"]
            assert (
                role in valid_roles
            ), f"Beat {beat['beat_id']} has invalid narrative_role: {role!r}"


def test_narrative_role_coverage() -> None:
    record = _load_scene_beat_plan()
    roles = set()
    for beat in record["source_beats"]:
        if "narrative_role" in beat:
            roles.add(beat["narrative_role"])

    # Expect at least establish, action, dialogue, hold, transition
    expected_roles = {"establish", "action", "dialogue"}
    assert expected_roles.issubset(
        roles
    ), f"Missing expected roles. Found: {roles}, expected at least: {expected_roles}"


# ---------------------------------------------------------------------------
# Boolean Flags (may_merge_with_next, splittable)
# ---------------------------------------------------------------------------


def test_may_merge_with_next_is_boolean() -> None:
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        assert isinstance(
            beat.get("may_merge_with_next"), bool
        ), f"Beat {beat['beat_id']} may_merge_with_next must be boolean"


def test_splittable_is_boolean() -> None:
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        assert isinstance(
            beat.get("splittable"), bool
        ), f"Beat {beat['beat_id']} splittable must be boolean"


def test_splittable_true_only_for_long_hold() -> None:
    """Rule: only long_hold beats should have splittable: true."""
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        if beat.get("splittable"):
            assert (
                beat.get("semantic_duration_hint") == "long_hold"
            ), f"Beat {beat['beat_id']} has splittable=true but semantic_duration_hint != long_hold"


# ---------------------------------------------------------------------------
# No Kling-Bound Fields
# ---------------------------------------------------------------------------


def test_no_kling_shot_fields() -> None:
    """Ensure scene_beat_plan does not contain Kling-bound duration or packing fields."""
    record = _load_scene_beat_plan()
    forbidden_kling_fields = {
        "clip_count",
        "shots",
        "total_duration_seconds",
        "source_beat_ids",
        "omni_clip_plan_ref",
        "prompt_record_ref",
        "continuity_input_mode",
    }

    # Scene level
    found = set(record.keys()) & forbidden_kling_fields
    assert (
        not found
    ), f"scene_beat_plan has forbidden Kling-bound fields at scene level: {found}"

    # Beat level
    for beat in record["source_beats"]:
        found = set(beat.keys()) & forbidden_kling_fields
        assert (
            not found
        ), f"Beat {beat['beat_id']} has forbidden Kling-bound fields: {found}"


# ---------------------------------------------------------------------------
# Beat Count and Content Quality
# ---------------------------------------------------------------------------


def test_beat_count_minimum() -> None:
    record = _load_scene_beat_plan()
    assert (
        len(record["source_beats"]) >= 15
    ), f"Expected at least 15 source beats, got {len(record['source_beats'])}"


def test_all_beats_have_content() -> None:
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        content = beat.get("content", "").strip()
        assert content, f"Beat {beat['beat_id']} has empty or missing content"
        assert len(content) > 10, f"Beat {beat['beat_id']} content is too short: {content!r}"


def test_all_beats_have_semantic_duration_hint() -> None:
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        assert "semantic_duration_hint" in beat, (
            f"Beat {beat['beat_id']} missing semantic_duration_hint"
        )


def test_all_beats_have_merge_and_split_flags() -> None:
    record = _load_scene_beat_plan()
    for beat in record["source_beats"]:
        assert "may_merge_with_next" in beat, (
            f"Beat {beat['beat_id']} missing may_merge_with_next"
        )
        assert "splittable" in beat, f"Beat {beat['beat_id']} missing splittable"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_provenance_present() -> None:
    record = _load_scene_beat_plan()
    assert "provenance" in record, "Record must have provenance"
    assert "created_by" in record["provenance"]
    assert "created_at" in record["provenance"]


def test_provenance_created_by() -> None:
    record = _load_scene_beat_plan()
    assert record["provenance"]["created_by"] == "hknbb"


# ---------------------------------------------------------------------------
# Scene-Specific Coverage: Kitchen to Jin's Room Journey
# ---------------------------------------------------------------------------


def test_kitchen_to_jins_room_journey_complete() -> None:
    """Verify the scene's spatial and narrative journey is intact."""
    record = _load_scene_beat_plan()
    beat_ids = [beat["beat_id"] for beat in record["source_beats"]]

    # Expected journey markers
    journey_markers = [
        "ESTABLISH_KITCHEN",
        "CORRIDOR_TRANSITION",
        "JINS_ROOM_ESTABLISH",
    ]

    for marker in journey_markers:
        assert (
            marker in beat_ids
        ), f"Journey marker beat {marker!r} not found in beat_ids"


def test_frame_discovery_arc_complete() -> None:
    """Verify the frame discovery arc (notice, straighten, evidence)."""
    record = _load_scene_beat_plan()
    beat_ids = [beat["beat_id"] for beat in record["source_beats"]]

    frame_arc = [
        "NADIA_BIRTA_PASSING",  # stops at frame
        "OFF_ANGLE_DISCOVERY",  # notices angle
        "FRAME_STRAIGHTENING",  # straightens
        "DUST_SHADOW_EVIDENCE",  # sees evidence of move
    ]

    for beat_id in frame_arc:
        assert beat_id in beat_ids, f"Frame discovery arc beat {beat_id!r} not found"

    # Verify ordering
    indices = [beat_ids.index(b) for b in frame_arc]
    assert indices == sorted(indices), "Frame discovery arc is out of order"
