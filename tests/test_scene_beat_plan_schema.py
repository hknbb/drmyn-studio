"""
A3 tests: scene_beat_plan schema validation (schema_version 0.x-draft).

Covers:
- Schema file exists and is valid JSON with required structure.
- Minimal valid records with various semantic_duration_hint values.
- beat_id pattern enforced (alphanumeric + underscore only).
- semantic_duration_hint enum validated (short_insert, normal, long_hold).
- narrative_role enum validated (establish, action, dialogue, hold, transition, pulse_check, insert).
- may_merge_with_next and splittable boolean flags validated.
- additionalProperties=false rejects unknown fields.
- Required fields enforced.
- Semantic constraint: short_insert with may_merge_with_next:false is allowed but implies beat should
  stay atomic unless forced (packer decision); splittable:true on short_insert is not a JSON Schema error
  but logically contradictory (source: plan §13 — short_insert is sub-3s detail, never standalone).
- No duration_seconds field present (explicitly forbidden in plan; enforced by schema not having it).
- Multiple beats per scene with unique beat_ids.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SCHEMA_PATH = REPO_ROOT / "schemas" / "scene_beat_plan.schema.json"


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _minimal_record(overrides: dict | None = None) -> dict:
    base = {
        "schema_version": "0.x-draft",
        "record_type": "scene_beat_plan",
        "scene_id": "SC0001",
        "source_beats": [
            {
                "beat_id": "ESTABLISH_KITCHEN",
                "content": "Pan across kitchen counter, settling on Nadia's hands as she pours espresso.",
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
    """Helper to construct a beat with defaults."""
    return {
        "beat_id": beat_id,
        "content": f"Content for {beat_id}",
        "semantic_duration_hint": hint,
        "may_merge_with_next": merge,
        "splittable": split,
    }


# ---------------------------------------------------------------------------
# Schema structural tests
# ---------------------------------------------------------------------------


def test_schema_file_exists() -> None:
    assert SCHEMA_PATH.exists(), f"Schema not found: {SCHEMA_PATH}"


def test_schema_is_valid_json() -> None:
    schema = _load_schema()
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"


def test_schema_version_const_is_draft() -> None:
    schema = _load_schema()
    assert schema["properties"]["schema_version"]["const"] == "0.x-draft"


def test_schema_record_type_const() -> None:
    schema = _load_schema()
    assert schema["properties"]["record_type"]["const"] == "scene_beat_plan"


def test_schema_source_beats_required() -> None:
    schema = _load_schema()
    assert "source_beats" in schema["required"]
    assert schema["properties"]["source_beats"]["minItems"] == 1


def test_schema_no_duration_seconds_field() -> None:
    """Verify that duration_seconds is NOT present in schema properties at any level.
    This enforces the plan constraint: source beats are semantic, not temporal."""
    schema = _load_schema()
    # Top level: scene should not have duration_seconds
    assert "duration_seconds" not in schema["properties"], (
        "source scene must not have duration_seconds field"
    )
    # Beat level: neither in items properties nor in top-level beat schema
    beat_schema = schema["properties"]["source_beats"]["items"]
    assert "duration_seconds" not in beat_schema["properties"], (
        "source beat must not have duration_seconds field; durations computed by packer in A5/B6"
    )


def test_schema_rejects_top_level_duration_seconds() -> None:
    """Verify schema rejects duration_seconds at scene level."""
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"duration_seconds": 15})
    errors = list(validator.iter_errors(record))
    assert errors, "duration_seconds at scene level must be rejected by additionalProperties: false"


def test_schema_rejects_beat_level_duration_seconds() -> None:
    """Verify schema rejects duration_seconds on individual beats."""
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "beat_id": "TEST_BEAT",
                "content": "Test",
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
                "splittable": False,
                "duration_seconds": 5,  # NOT ALLOWED
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "duration_seconds on beat must be rejected by additionalProperties: false"


# ---------------------------------------------------------------------------
# Valid record tests
# ---------------------------------------------------------------------------


def test_minimal_record_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(_minimal_record()))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_short_insert_beat_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            _beat("SHORT_HAND_INSERT", hint="short_insert", merge=True, split=False)
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_long_hold_beat_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            _beat("ESTABLISH_BEDROOM", hint="long_hold", merge=False, split=True)
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_all_narrative_roles_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    beats = [
        {**_beat("ESTABLISH"), "narrative_role": "establish"},
        {**_beat("ACTION"), "narrative_role": "action"},
        {**_beat("DIALOGUE"), "narrative_role": "dialogue"},
        {**_beat("HOLD"), "narrative_role": "hold"},
        {**_beat("TRANSITION"), "narrative_role": "transition"},
        {**_beat("PULSE"), "narrative_role": "pulse_check"},
        {**_beat("INSERT"), "narrative_role": "insert"},
    ]
    record = _minimal_record({"source_beats": beats})
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_multiple_beats_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            _beat("BEAT_1", hint="normal", merge=False, split=False),
            _beat("BEAT_2", hint="short_insert", merge=True, split=False),
            _beat("BEAT_3", hint="long_hold", merge=False, split=True),
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_notes_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "notes": "This scene establishes the domestic setting and Nadia's morning routine.",
        "source_beats": [
            {
                **_beat("ESTABLISH_KITCHEN"),
                "notes": "Emphasize warm lighting and small-town quietness."
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


# ---------------------------------------------------------------------------
# Invalid record tests
# ---------------------------------------------------------------------------


def test_invalid_beat_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("beat-1", "beat.1", "123beat", "beat@2", "BEAT 1"):
        record = _minimal_record({
            "source_beats": [_beat(bad_id)]  # type: ignore
        })
        errors = list(validator.iter_errors(record))
        assert errors, f"beat_id={bad_id!r} should fail pattern validation"


def test_empty_beat_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "beat_id": ""
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Empty beat_id must fail minLength validation"


def test_beat_id_over_max_length_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "beat_id": "A" * 51  # max is 50
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "beat_id > 50 chars must fail maxLength validation"


def test_empty_content_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "content": ""
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Empty content must fail minLength validation"


def test_invalid_semantic_duration_hint_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "semantic_duration_hint": "microsecond"  # Invalid
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Invalid semantic_duration_hint must fail enum validation"


def test_invalid_narrative_role_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "narrative_role": "exposition"  # Not in enum
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Invalid narrative_role must fail enum validation"


def test_may_merge_with_next_not_boolean_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "may_merge_with_next": "yes"  # type: ignore
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "may_merge_with_next non-boolean must fail type validation"


def test_splittable_not_boolean_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "splittable": "no"  # type: ignore
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "splittable non-boolean must fail type validation"


def test_unknown_beat_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                **_beat("TEST"),
                "duration_seconds": 5  # Unknown field
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Unknown beat field must be rejected by additionalProperties: false"


def test_missing_scene_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["scene_id"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing scene_id must fail"


def test_invalid_scene_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("SCENE0001", "S0001", "SC001", "SC00001"):
        record = _minimal_record({"scene_id": bad_id})
        errors = list(validator.iter_errors(record))
        assert errors, f"scene_id={bad_id!r} should fail pattern validation (must be SC\\d{{4}})"


def test_empty_source_beats_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"source_beats": []})
    errors = list(validator.iter_errors(record))
    assert errors, "Empty source_beats must fail minItems validation"


def test_missing_beat_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "content": "Test",
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
                "splittable": False,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing beat_id must fail"


def test_missing_content_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "beat_id": "TEST",
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
                "splittable": False,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing content must fail"


def test_missing_semantic_duration_hint_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "beat_id": "TEST",
                "content": "Test",
                "may_merge_with_next": False,
                "splittable": False,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing semantic_duration_hint must fail"


def test_missing_may_merge_with_next_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "beat_id": "TEST",
                "content": "Test",
                "semantic_duration_hint": "normal",
                "splittable": False,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing may_merge_with_next must fail"


def test_missing_splittable_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "source_beats": [
            {
                "beat_id": "TEST",
                "content": "Test",
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing splittable must fail"


def test_missing_provenance_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["provenance"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing provenance must fail"
