"""
A4 tests: dialogue_beats schema validation (schema_version 0.x-draft).

Covers:
- Schema file exists and is valid JSON with required structure.
- Minimal valid records pass (single dialogue line, multiple lines, various line types).
- record_type constant enforcement.
- schema_version constant enforcement.
- scene_id pattern validation (SC\d{4}).
- line_id pattern enforcement (DLG_[A-Z0-9_]+).
- target_beat_id pattern validation (references scene_beat_plan.yaml beat IDs).
- speaker_element_id pattern validation (C\d{2}).
- speaker_kling_alias pattern validation (@[A-Za-z0-9_]+, requires @).
- line_type enum validated (spoken, interrupted, offscreen, implied).
- native_audio_readiness enum validated (blocked, metadata_only, ready).
- kling_native_audio block enforcement: external_tts_allowed and adr_vendor_allowed const false.
- additionalProperties=false rejects TTS/ADR vendor fields, duration_seconds, clip_count, lifecycle keys.
- Missing required fields rejected.
- Hard rule: external_tts_allowed must be false; adr_vendor_allowed must be false.
- No duration_seconds, clip_count, shots, total_duration_seconds, or lifecycle keys permitted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SCHEMA_PATH = REPO_ROOT / "schemas" / "dialogue_beats.schema.json"

FORBIDDEN_LIFECYCLE_KEYS = {
    "pack_status",
    "canon_lock",
    "approved",
    "locked",
    "selected",
    "selected_take",
}


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _minimal_record(overrides: dict | None = None) -> dict:
    base = {
        "schema_version": "0.x-draft",
        "record_type": "dialogue_beats",
        "scene_id": "SC0001",
        "source_scene_beat_plan_ref": "planning/scenes/SC0001/scene_beat_plan.yaml",
        "source_element_bindings_ref": "visual_dev/omni_sets/SC0001/element_bindings.yaml",
        "dialogue_lines": [
            {
                "line_id": "DLG_NADIA_SLEEP_01",
                "target_beat_id": "DIALOGUE_SLEEP_ACCUSATION",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Nadia",
                "line_text": "You didn't sleep again.",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ],
        "ambient_sound_prompt": "Early morning kitchen quiet with subtle hallway ambience.",
        "kling_native_audio": {
            "enabled": True,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
        "provenance": {
            "created_by": "hknbb",
            "created_at": "2026-05-08T00:00:00Z",
        },
    }
    if overrides:
        base.update(overrides)
    return base


def _dialogue_line(
    line_id: str = "DLG_TEST_01",
    target_beat_id: str = "TEST_BEAT",
    speaker_element_id: str = "C01",
    speaker_kling_alias: str = "@Speaker",
    line_text: str = "Test dialogue line.",
    line_type: str = "spoken",
    native_audio_readiness: str = "metadata_only",
    dialogue_required: bool = True,
) -> dict:
    """Helper to construct a dialogue line."""
    return {
        "line_id": line_id,
        "target_beat_id": target_beat_id,
        "speaker_element_id": speaker_element_id,
        "speaker_kling_alias": speaker_kling_alias,
        "line_text": line_text,
        "line_type": line_type,
        "native_audio_readiness": native_audio_readiness,
        "dialogue_required": dialogue_required,
    }


# ---------------------------------------------------------------------------
# Schema Structural Tests
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
    assert schema["properties"]["record_type"]["const"] == "dialogue_beats"


def test_schema_dialogue_lines_required() -> None:
    schema = _load_schema()
    assert "dialogue_lines" in schema["required"]
    assert schema["properties"]["dialogue_lines"]["minItems"] == 1


def test_schema_has_no_forbidden_lifecycle_keys() -> None:
    schema = _load_schema()
    schema_props = set(schema.get("properties", {}).keys())
    intersection = schema_props & FORBIDDEN_LIFECYCLE_KEYS
    assert not intersection, (
        f"dialogue_beats schema must not contain lifecycle keys: {intersection}"
    )


def test_schema_rejects_duration_seconds_field() -> None:
    """Verify that duration_seconds is NOT present in schema properties."""
    schema = _load_schema()
    assert "duration_seconds" not in schema["properties"], (
        "dialogue_beats must not have duration_seconds field"
    )
    # Also check dialogue_lines items
    line_schema = schema["properties"]["dialogue_lines"]["items"]
    assert "duration_seconds" not in line_schema["properties"], (
        "dialogue line must not have duration_seconds field"
    )


# ---------------------------------------------------------------------------
# Valid Record Tests
# ---------------------------------------------------------------------------


def test_minimal_record_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(_minimal_record()))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_multiple_dialogue_lines_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            _dialogue_line("DLG_NADIA_SLEEP_01", "DIALOGUE_SLEEP_ACCUSATION", "C01", "@Nadia", "You didn't sleep again.", "spoken", "metadata_only", True),
            _dialogue_line("DLG_BIRTA_SLEEP_01", "DIALOGUE_SLEEP_ACCUSATION", "C03", "@Birta", "You slept the way you fold laundry.", "spoken", "metadata_only", True),
            _dialogue_line("DLG_NADIA_FORMULA", "DIALOGUE_FORMULA_VITAMIN", "C01", "@Nadia", "Jin's formula. There's a new tin in the second shelf.", "spoken", "metadata_only", True),
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_all_line_types_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    lines = [
        _dialogue_line(f"DLG_TEST_{i:02d}", "TEST_BEAT", "C01", "@Speaker", f"Line {i}", line_type, "metadata_only", True)
        for i, line_type in enumerate(["spoken", "interrupted", "offscreen", "implied"], 1)
    ]
    record = _minimal_record({"dialogue_lines": lines})
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_all_audio_readiness_states_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    lines = [
        _dialogue_line(f"DLG_TEST_{i:02d}", "TEST_BEAT", "C01", "@Speaker", f"Line {i}", "spoken", readiness, True)
        for i, readiness in enumerate(["blocked", "metadata_only", "ready"], 1)
    ]
    record = _minimal_record({"dialogue_lines": lines})
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_optional_dialogue_fields_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                **_dialogue_line(),
                "delivery_note": "Flat, no inflection.",
                "subtext_note": "Exhaustion masked by politeness.",
                "source_quote_ref": "source/screenplay/closing_price.fountain:line_29",
                "pronunciation_note": "Nadia: NAH-dee-ah",
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_notes_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "notes": "SC0001 dialogue layer: 5 dialogue beats, all characters use Kling-native audio. No external TTS."
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


def test_record_with_dialogue_not_required_passes() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "dialogue_required": False}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors == [], "\n".join(e.message for e in errors)


# ---------------------------------------------------------------------------
# Invalid Record Tests (Constants and Patterns)
# ---------------------------------------------------------------------------


def test_wrong_record_type_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"record_type": "scene_beat_plan"})
    errors = list(validator.iter_errors(record))
    assert errors, "record_type other than dialogue_beats must fail"


def test_wrong_schema_version_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"schema_version": "1.0"})
    errors = list(validator.iter_errors(record))
    assert errors, "schema_version other than 0.x-draft must fail"


def test_invalid_scene_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("SCENE0001", "S0001", "SC001", "SC00001"):
        record = _minimal_record({"scene_id": bad_id})
        errors = list(validator.iter_errors(record))
        assert errors, f"scene_id={bad_id!r} should fail pattern validation"


def test_invalid_line_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("NADIA_SLEEP", "dlg_nadia", "DLG-NADIA", "123DLG"):
        record = _minimal_record({
            "dialogue_lines": [
                {**_dialogue_line(), "line_id": bad_id}
            ]
        })
        errors = list(validator.iter_errors(record))
        assert errors, f"line_id={bad_id!r} should fail pattern validation"


def test_invalid_target_beat_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("dialogue-beat", "BEAT.1", "beat_1"):
        record = _minimal_record({
            "dialogue_lines": [
                {**_dialogue_line(), "target_beat_id": bad_id}
            ]
        })
        errors = list(validator.iter_errors(record))
        assert errors, f"target_beat_id={bad_id!r} should fail pattern validation"


def test_invalid_speaker_element_id_pattern_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    for bad_id in ("Nadia", "c01", "CHAR01", "C001"):
        record = _minimal_record({
            "dialogue_lines": [
                {**_dialogue_line(), "speaker_element_id": bad_id}
            ]
        })
        errors = list(validator.iter_errors(record))
        assert errors, f"speaker_element_id={bad_id!r} should fail pattern validation"


def test_speaker_kling_alias_without_at_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "speaker_kling_alias": "Nadia"}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "speaker_kling_alias without @ must fail pattern validation"


def test_speaker_kling_alias_with_invalid_chars_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "speaker_kling_alias": "@Nadia-Vale"}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "speaker_kling_alias with dash must fail pattern validation"


# ---------------------------------------------------------------------------
# Line Type and Readiness Enum Tests
# ---------------------------------------------------------------------------


def test_invalid_line_type_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "line_type": "monologue"}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Invalid line_type must fail enum validation"


def test_invalid_native_audio_readiness_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "native_audio_readiness": "pending"}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Invalid native_audio_readiness must fail enum validation"


def test_dialogue_required_not_boolean_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "dialogue_required": "yes"}  # type: ignore
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "dialogue_required non-boolean must fail type validation"


# ---------------------------------------------------------------------------
# Kling Native Audio Block Tests
# ---------------------------------------------------------------------------


def test_external_tts_allowed_true_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "kling_native_audio": {
            "enabled": True,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": True,
            "adr_vendor_allowed": False,
        }
    })
    errors = list(validator.iter_errors(record))
    assert errors, "external_tts_allowed true must fail (const false)"


def test_adr_vendor_allowed_true_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "kling_native_audio": {
            "enabled": True,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": True,
        }
    })
    errors = list(validator.iter_errors(record))
    assert errors, "adr_vendor_allowed true must fail (const false)"


# ---------------------------------------------------------------------------
# Forbidden Vendor Field Tests
# ---------------------------------------------------------------------------


def test_elevenlabs_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"elevenlabs_api_key": "xyz"})
    errors = list(validator.iter_errors(record))
    assert errors, "elevenlabs_api_key must be rejected by additionalProperties: false"


def test_external_tts_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"external_tts_provider": "some_vendor"})
    errors = list(validator.iter_errors(record))
    assert errors, "external_tts_provider must be rejected by additionalProperties: false"


def test_tts_vendor_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"tts_vendor": "SomeVendor"})
    errors = list(validator.iter_errors(record))
    assert errors, "tts_vendor must be rejected by additionalProperties: false"


def test_adr_vendor_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"adr_vendor": "ADRVendor"})
    errors = list(validator.iter_errors(record))
    assert errors, "adr_vendor must be rejected by additionalProperties: false"


def test_voice_clone_vendor_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"voice_clone_vendor": "CloneVendor"})
    errors = list(validator.iter_errors(record))
    assert errors, "voice_clone_vendor must be rejected by additionalProperties: false"


# ---------------------------------------------------------------------------
# Forbidden Kling-Bound Field Tests
# ---------------------------------------------------------------------------


def test_duration_seconds_at_scene_level_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"duration_seconds": 5})
    errors = list(validator.iter_errors(record))
    assert errors, "duration_seconds at scene level must be rejected"


def test_duration_seconds_at_line_level_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {**_dialogue_line(), "duration_seconds": 3}
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "duration_seconds at line level must be rejected"


def test_clip_count_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"clip_count": 3})
    errors = list(validator.iter_errors(record))
    assert errors, "clip_count must be rejected by additionalProperties: false"


def test_shots_field_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"shots": []})
    errors = list(validator.iter_errors(record))
    assert errors, "shots must be rejected by additionalProperties: false"


def test_total_duration_seconds_rejected() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"total_duration_seconds": 15})
    errors = list(validator.iter_errors(record))
    assert errors, "total_duration_seconds must be rejected by additionalProperties: false"


# ---------------------------------------------------------------------------
# Missing Required Field Tests
# ---------------------------------------------------------------------------


def test_missing_schema_version_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["schema_version"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing schema_version must fail"


def test_missing_record_type_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["record_type"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing record_type must fail"


def test_missing_scene_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["scene_id"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing scene_id must fail"


def test_missing_source_scene_beat_plan_ref_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["source_scene_beat_plan_ref"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing source_scene_beat_plan_ref must fail"


def test_missing_source_element_bindings_ref_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["source_element_bindings_ref"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing source_element_bindings_ref must fail"


def test_missing_dialogue_lines_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["dialogue_lines"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing dialogue_lines must fail"


def test_empty_dialogue_lines_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({"dialogue_lines": []})
    errors = list(validator.iter_errors(record))
    assert errors, "Empty dialogue_lines must fail minItems validation"


def test_missing_ambient_sound_prompt_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["ambient_sound_prompt"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing ambient_sound_prompt must fail"


def test_missing_kling_native_audio_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["kling_native_audio"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing kling_native_audio must fail"


def test_missing_provenance_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record()
    del record["provenance"]
    errors = list(validator.iter_errors(record))
    assert errors, "Missing provenance must fail"


# ---------------------------------------------------------------------------
# Dialogue Line Required Field Tests
# ---------------------------------------------------------------------------


def test_missing_line_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing line_id must fail"


def test_missing_target_beat_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing target_beat_id must fail"


def test_missing_speaker_element_id_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing speaker_element_id must fail"


def test_missing_speaker_kling_alias_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "line_text": "Test",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing speaker_kling_alias must fail"


def test_missing_line_text_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing line_text must fail"


def test_missing_line_type_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "native_audio_readiness": "metadata_only",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing line_type must fail"


def test_missing_native_audio_readiness_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "line_type": "spoken",
                "dialogue_required": True,
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing native_audio_readiness must fail"


def test_missing_dialogue_required_fails() -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    record = _minimal_record({
        "dialogue_lines": [
            {
                "line_id": "DLG_TEST",
                "target_beat_id": "TEST",
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Speaker",
                "line_text": "Test",
                "line_type": "spoken",
                "native_audio_readiness": "metadata_only",
            }
        ]
    })
    errors = list(validator.iter_errors(record))
    assert errors, "Missing dialogue_required must fail"
