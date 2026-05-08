"""
A3.1 tests: scene_beat_plan semantic validator (cross-beat rules).

Covers:
- beat_id uniqueness within a single scene (enforced by Python validator)
- duplicate beat_id detection with clear error messages
- duration_seconds defensive rejection at scene and beat levels
- batch validation across multiple scene records
- cross-scene beat_ids are allowed (uniqueness is per-scene, not global)
- empty records return no errors
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validators.validate_scene_beat_plan import (
    SceneBeatPlanValidationError,
    validate_scene_beat_plan,
    validate_scene_beat_plan_batch,
)


def _minimal_record(overrides: dict | None = None) -> dict:
    """Create a minimal valid scene_beat_plan record."""
    base = {
        "schema_version": "0.x-draft",
        "record_type": "scene_beat_plan",
        "scene_id": "SC0001",
        "source_beats": [
            {
                "beat_id": "ESTABLISH_KITCHEN",
                "content": "Pan across kitchen counter.",
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
                "splittable": False,
            }
        ],
        "provenance": {
            "created_by": "hknbb",
            "created_at": "2026-05-08T00:00:00Z",
        },
    }
    if overrides:
        base.update(overrides)
    return base


def _beat(beat_id: str, hint: str = "normal", merge: bool = False, split: bool = False) -> dict:
    """Helper to construct a beat."""
    return {
        "beat_id": beat_id,
        "content": f"Content for {beat_id}",
        "semantic_duration_hint": hint,
        "may_merge_with_next": merge,
        "splittable": split,
    }


# ---------------------------------------------------------------------------
# Valid record tests
# ---------------------------------------------------------------------------


def test_valid_single_beat_passes() -> None:
    """Minimal valid record with single beat."""
    record = _minimal_record()
    errors = validate_scene_beat_plan(record)
    assert errors == [], f"Expected no errors, got {errors}"


def test_valid_multiple_unique_beats_passes() -> None:
    """Record with multiple beats, all unique beat_ids."""
    record = _minimal_record({
        "source_beats": [
            _beat("BEAT_1"),
            _beat("BEAT_2"),
            _beat("BEAT_3"),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert errors == [], f"Expected no errors, got {errors}"


def test_valid_various_semantic_hints_passes() -> None:
    """Record with all semantic_duration_hint values."""
    record = _minimal_record({
        "source_beats": [
            _beat("SHORT_INSERT", hint="short_insert", merge=True),
            _beat("NORMAL_BEAT", hint="normal"),
            _beat("LONG_HOLD", hint="long_hold", split=True),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert errors == [], f"Expected no errors, got {errors}"


def test_empty_source_beats_passes() -> None:
    """Empty source_beats array passes validator (schema already rejects minItems: 1)."""
    record = _minimal_record({"source_beats": []})
    errors = validate_scene_beat_plan(record)
    # Validator does not enforce minItems; schema handles that
    assert errors == [], f"Expected no errors for empty array, got {errors}"


# ---------------------------------------------------------------------------
# Invalid record tests: beat_id uniqueness
# ---------------------------------------------------------------------------


def test_duplicate_beat_id_fails() -> None:
    """Two beats with same beat_id must fail."""
    record = _minimal_record({
        "source_beats": [
            _beat("DUPLICATE_BEAT"),
            _beat("DUPLICATE_BEAT"),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert errors[0].error_code == "DUPLICATE_BEAT_ID"
    assert "DUPLICATE_BEAT" in errors[0].message
    assert "SC0001" in errors[0].message


def test_three_beats_two_duplicates_fails() -> None:
    """Three beats with one duplicate pair."""
    record = _minimal_record({
        "source_beats": [
            _beat("UNIQUE_BEAT"),
            _beat("DUPLICATE"),
            _beat("DUPLICATE"),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert errors[0].error_code == "DUPLICATE_BEAT_ID"


def test_three_duplicate_beat_ids_fails() -> None:
    """Three beats with same beat_id (multiple occurrences of same ID)."""
    record = _minimal_record({
        "source_beats": [
            _beat("TRIPLE"),
            _beat("TRIPLE"),
            _beat("TRIPLE"),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 2, f"Expected 2 errors (2nd and 3rd occurrence), got {len(errors)}"
    assert all(e.error_code == "DUPLICATE_BEAT_ID" for e in errors)


def test_duplicate_beat_id_error_includes_scene_id() -> None:
    """Error message includes scene_id and beat_id."""
    record = _minimal_record({
        "scene_id": "SC0042",
        "source_beats": [
            _beat("DUPLICATE"),
            _beat("DUPLICATE"),
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1
    error_str = str(errors[0])
    assert "SC0042" in error_str
    assert "DUPLICATE" in error_str


# ---------------------------------------------------------------------------
# Invalid record tests: duration_seconds
# ---------------------------------------------------------------------------


def test_duration_seconds_at_scene_level_fails() -> None:
    """duration_seconds at scene level is rejected (defensive check)."""
    record = _minimal_record({"duration_seconds": 15})
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1
    assert errors[0].error_code == "DURATION_SECONDS_AT_SCENE"
    assert "duration_seconds" in errors[0].message


def test_duration_seconds_in_beat_fails() -> None:
    """duration_seconds inside a beat is rejected (defensive check)."""
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST_BEAT"),
                "duration_seconds": 5,
            }
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1
    assert errors[0].error_code == "DURATION_SECONDS_IN_BEAT"
    assert "TEST_BEAT" in errors[0].message


def test_duration_seconds_in_multiple_beats_fails() -> None:
    """duration_seconds in multiple beats generates multiple errors."""
    record = _minimal_record({
        "source_beats": [
            {**_beat("BEAT_1"), "duration_seconds": 5},
            {**_beat("BEAT_2"), "duration_seconds": 7},
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 2
    assert all(e.error_code == "DURATION_SECONDS_IN_BEAT" for e in errors)


def test_both_scene_and_beat_duration_seconds_fails() -> None:
    """If both scene-level and beat-level duration_seconds present, both errors reported."""
    record = _minimal_record({
        "duration_seconds": 15,
        "source_beats": [
            {
                **_beat("BEAT"),
                "duration_seconds": 5,
            }
        ]
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 2
    error_codes = {e.error_code for e in errors}
    assert "DURATION_SECONDS_AT_SCENE" in error_codes
    assert "DURATION_SECONDS_IN_BEAT" in error_codes


# ---------------------------------------------------------------------------
# Batch validation tests
# ---------------------------------------------------------------------------


def test_batch_validation_all_valid() -> None:
    """Batch with all valid records returns empty dict."""
    records = [
        _minimal_record({"scene_id": "SC0001"}),
        _minimal_record({"scene_id": "SC0002"}),
    ]
    errors = validate_scene_beat_plan_batch(records)
    assert errors == {}


def test_batch_validation_one_invalid_scene() -> None:
    """Batch with one scene having errors."""
    records = [
        _minimal_record({"scene_id": "SC0001"}),
        _minimal_record({
            "scene_id": "SC0002",
            "source_beats": [_beat("DUP"), _beat("DUP")],
        }),
    ]
    errors = validate_scene_beat_plan_batch(records)
    assert len(errors) == 1
    assert "SC0002" in errors
    assert len(errors["SC0002"]) == 1


def test_batch_validation_multiple_invalid_scenes() -> None:
    """Batch with multiple scenes having errors."""
    records = [
        _minimal_record({
            "scene_id": "SC0001",
            "source_beats": [_beat("DUP"), _beat("DUP")],
        }),
        _minimal_record({
            "scene_id": "SC0002",
            "duration_seconds": 999,
        }),
    ]
    errors = validate_scene_beat_plan_batch(records)
    assert len(errors) == 2
    assert "SC0001" in errors
    assert "SC0002" in errors


def test_batch_validation_same_beat_id_different_scenes_allowed() -> None:
    """Same beat_id in different scenes is allowed (uniqueness is per-scene)."""
    records = [
        _minimal_record({
            "scene_id": "SC0001",
            "source_beats": [_beat("ESTABLISH")],
        }),
        _minimal_record({
            "scene_id": "SC0002",
            "source_beats": [_beat("ESTABLISH")],
        }),
    ]
    errors = validate_scene_beat_plan_batch(records)
    assert errors == {}, f"Expected no errors for same beat_id in different scenes, got {errors}"


def test_batch_validation_empty_batch() -> None:
    """Empty batch returns no errors."""
    errors = validate_scene_beat_plan_batch([])
    assert errors == {}


# ---------------------------------------------------------------------------
# Exception type and message formatting tests
# ---------------------------------------------------------------------------


def test_validation_error_type() -> None:
    """Errors are instances of SceneBeatPlanValidationError."""
    record = _minimal_record({
        "source_beats": [_beat("DUP"), _beat("DUP")]
    })
    errors = validate_scene_beat_plan(record)
    assert all(isinstance(e, SceneBeatPlanValidationError) for e in errors)


def test_validation_error_fields() -> None:
    """SceneBeatPlanValidationError has scene_id, error_code, message."""
    record = _minimal_record({
        "scene_id": "SC0099",
        "source_beats": [_beat("TEST"), _beat("TEST")],
    })
    errors = validate_scene_beat_plan(record)
    assert len(errors) == 1
    error = errors[0]
    assert error.scene_id == "SC0099"
    assert error.error_code == "DUPLICATE_BEAT_ID"
    assert isinstance(error.message, str)
    assert len(error.message) > 0


def test_validation_error_string_representation() -> None:
    """Error string representation includes scene_id and code."""
    record = _minimal_record({
        "scene_id": "SC0077",
        "source_beats": [_beat("TEST"), _beat("TEST")],
    })
    errors = validate_scene_beat_plan(record)
    error_str = str(errors[0])
    assert "SC0077" in error_str
    assert "DUPLICATE_BEAT_ID" in error_str
