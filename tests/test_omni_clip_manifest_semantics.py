"""
Tests for omni_clip_manifest semantic validation.

Validates cross-field rules that JSON Schema cannot enforce:
1. sum(shots[].duration_seconds) == total_duration_seconds
2. All source_beat_ids exist in scene_beat_plan
3. All dialogue_line_ids exist in dialogue_beats
4. No unsplittable beat is split across shots
5. frame_input_active requires frame references
6. kling_native_audio forbids external TTS/ADR
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validators.validate_omni_clip_manifest import (
    validate_omni_clip_manifest,
    OmniClipManifestValidationError,
)


@pytest.fixture
def repo_root():
    """Return repo root path."""
    return Path(__file__).parent.parent


def _minimal_omni_clip_manifest(**overrides):
    """Create minimal valid omni_clip_manifest record."""
    record = {
        "schema_version": "0.x-draft",
        "record_type": "omni_clip_manifest",
        "scene_id": "SC0001",
        "clip_id": "CLIP_SC0001_01",
        "source_scene_beat_plan_ref": "planning/scenes/SC0001/scene_beat_plan.yaml",
        "source_dialogue_beats_ref": "planning/scenes/SC0001/dialogue_beats.yaml",
        "total_duration_seconds": 5,
        "continuity_input_mode": "metadata_only",
        "shots": [
            {
                "shot_id": "SHOT_SC0001_01_A",
                "duration_seconds": 5,
                "source_beat_ids": ["ESTABLISH_KITCHEN"],
                "prompt_action": "Establish kitchen",
                "duration_reason": "Kitchen establish",
            }
        ],
        "kling_native_audio": {
            "enabled": False,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
        "provenance": {
            "created_by": "test",
            "created_at": "2026-05-08T22:00:00Z",
        },
    }
    record.update(overrides)
    return record


def test_valid_single_shot_manifest(repo_root):
    """Valid single-shot manifest passes validation."""
    record = _minimal_omni_clip_manifest()
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_valid_multi_shot_manifest(repo_root):
    """Valid multi-shot manifest with matching duration passes."""
    record = _minimal_omni_clip_manifest(total_duration_seconds=10)
    record["shots"] = [
        {
            "shot_id": "SHOT_SC0001_01_A",
            "duration_seconds": 5,
            "source_beat_ids": ["ESTABLISH_KITCHEN"],
            "prompt_action": "Kitchen",
            "duration_reason": "First beat",
        },
        {
            "shot_id": "SHOT_SC0001_01_B",
            "duration_seconds": 5,
            "source_beat_ids": ["NADIA_PASSAGE_MOVEMENT"],
            "prompt_action": "Movement",
            "duration_reason": "Second beat",
        },
    ]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_duration_mismatch_error(repo_root):
    """Duration mismatch between total and sum(shots) fails."""
    record = _minimal_omni_clip_manifest(total_duration_seconds=10)  # but shots total 5
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "DURATION_MISMATCH" in str(errors[0])


def test_unknown_beat_id_error(repo_root):
    """Unknown source_beat_id in shot fails."""
    record = _minimal_omni_clip_manifest()
    record["shots"][0]["source_beat_ids"] = ["UNKNOWN_BEAT_ID"]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "UNKNOWN_BEAT_ID" in str(errors[0])


def test_unknown_dialogue_line_id_error(repo_root):
    """Unknown dialogue_line_id in shot fails."""
    record = _minimal_omni_clip_manifest()
    record["shots"][0]["dialogue_line_ids"] = ["DLG_UNKNOWN_LINE"]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "UNKNOWN_LINE_ID" in str(errors[0])


def test_valid_known_dialogue_line_id(repo_root):
    """Known dialogue_line_id from SC0001 passes."""
    record = _minimal_omni_clip_manifest()
    record["shots"][0]["dialogue_line_ids"] = ["DLG_BIRTA_SLEEP_01"]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_unsplittable_beat_split_error(repo_root):
    """Unsplittable beat (splittable: false) split across shots fails."""
    record = _minimal_omni_clip_manifest(total_duration_seconds=10)
    record["shots"] = [
        {
            "shot_id": "SHOT_SC0001_01_A",
            "duration_seconds": 5,
            "source_beat_ids": ["FRAME_STRAIGHTENING"],  # splittable: false
            "prompt_action": "Part 1",
            "duration_reason": "Part of split beat",
        },
        {
            "shot_id": "SHOT_SC0001_01_B",
            "duration_seconds": 5,
            "source_beat_ids": ["FRAME_STRAIGHTENING"],  # same beat again
            "prompt_action": "Part 2",
            "duration_reason": "Rest of split beat",
        },
    ]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert any("UNSPLITTABLE_BEAT_SPLIT" in str(e) for e in errors)


def test_splittable_beat_split_allowed(repo_root):
    """Splittable beat (splittable: true) split across shots passes."""
    record = _minimal_omni_clip_manifest(total_duration_seconds=10)
    record["shots"] = [
        {
            "shot_id": "SHOT_SC0001_01_A",
            "duration_seconds": 5,
            "source_beat_ids": ["NADIA_JIN_OBSERVATION"],  # splittable: true
            "prompt_action": "Part 1",
            "duration_reason": "First part",
        },
        {
            "shot_id": "SHOT_SC0001_01_B",
            "duration_seconds": 5,
            "source_beat_ids": ["NADIA_JIN_OBSERVATION"],  # same beat
            "prompt_action": "Part 2",
            "duration_reason": "Continued observation",
        },
    ]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_frame_input_active_no_refs_error(repo_root):
    """frame_input_active without frame references fails."""
    record = _minimal_omni_clip_manifest(continuity_input_mode="frame_input_active")
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "FRAME_INPUT_ACTIVE_NO_REFS" in str(errors[0])


def test_frame_input_active_with_first_frame_passes(repo_root):
    """frame_input_active with first_frame_reference passes."""
    record = _minimal_omni_clip_manifest(continuity_input_mode="frame_input_active")
    record["first_frame_reference"] = {
        "frame_description": "Nadia in corridor",
    }
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_frame_input_active_with_last_frame_passes(repo_root):
    """frame_input_active with last_frame_reference passes."""
    record = _minimal_omni_clip_manifest(continuity_input_mode="frame_input_active")
    record["last_frame_reference"] = {
        "frame_description": "Nadia reaches door",
    }
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_metadata_only_without_frame_refs_passes(repo_root):
    """metadata_only mode without frame references passes."""
    record = _minimal_omni_clip_manifest(continuity_input_mode="metadata_only")
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_frame_input_eligible_without_frame_refs_passes(repo_root):
    """frame_input_eligible without frame references passes."""
    record = _minimal_omni_clip_manifest(continuity_input_mode="frame_input_eligible")
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_external_tts_allowed_error(repo_root):
    """external_tts_allowed: true fails validation."""
    record = _minimal_omni_clip_manifest()
    record["kling_native_audio"]["external_tts_allowed"] = True
    errors = validate_omni_clip_manifest(record, repo_root)
    assert any("EXTERNAL_TTS_ALLOWED" in str(e) for e in errors)


def test_adr_vendor_allowed_error(repo_root):
    """adr_vendor_allowed: true fails validation."""
    record = _minimal_omni_clip_manifest()
    record["kling_native_audio"]["adr_vendor_allowed"] = True
    errors = validate_omni_clip_manifest(record, repo_root)
    assert any("ADR_VENDOR_ALLOWED" in str(e) for e in errors)


def test_missing_scene_beat_plan_error(repo_root):
    """Missing source_scene_beat_plan_ref fails."""
    record = _minimal_omni_clip_manifest(
        source_scene_beat_plan_ref="nonexistent/scene_beat_plan.yaml"
    )
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "MISSING_SCENE_BEAT_PLAN" in str(errors[0])


def test_missing_dialogue_beats_error(repo_root):
    """Missing source_dialogue_beats_ref fails."""
    record = _minimal_omni_clip_manifest(
        source_dialogue_beats_ref="nonexistent/dialogue_beats.yaml"
    )
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 1
    assert "MISSING_DIALOGUE_BEATS" in str(errors[0])


def test_valid_manifest_with_multiple_dialogue_lines(repo_root):
    """Manifest with multiple dialogue lines in shot passes."""
    record = _minimal_omni_clip_manifest()
    record["shots"][0]["dialogue_line_ids"] = [
        "DLG_BIRTA_SLEEP_01",
        "DLG_NADIA_SLEEP_01",
        "DLG_BIRTA_SLEEP_02",
    ]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0


def test_batch_validation_no_dialogue_duplication(repo_root):
    """Batch validation passes with no dialogue line duplication."""
    from scripts.validators.validate_omni_clip_manifest import (
        validate_omni_clip_manifest_batch,
    )

    clip1 = _minimal_omni_clip_manifest(clip_id="CLIP_SC0001_01")
    clip1["shots"][0]["dialogue_line_ids"] = ["DLG_BIRTA_SLEEP_01"]

    clip2 = _minimal_omni_clip_manifest(clip_id="CLIP_SC0001_02")
    clip2["shots"][0]["dialogue_line_ids"] = ["DLG_NADIA_SLEEP_01"]

    errors_by_clip, cross_clip_violations = validate_omni_clip_manifest_batch(
        [clip1, clip2], repo_root
    )
    assert len(errors_by_clip) == 0
    assert len(cross_clip_violations) == 0


def test_batch_validation_dialogue_duplication_detected(repo_root):
    """Batch validation detects dialogue line duplication across clips."""
    from scripts.validators.validate_omni_clip_manifest import (
        validate_omni_clip_manifest_batch,
    )

    clip1 = _minimal_omni_clip_manifest(clip_id="CLIP_SC0001_01")
    clip1["shots"][0]["dialogue_line_ids"] = ["DLG_BIRTA_SLEEP_01"]

    clip2 = _minimal_omni_clip_manifest(clip_id="CLIP_SC0001_02")
    clip2["shots"][0]["dialogue_line_ids"] = ["DLG_BIRTA_SLEEP_01"]  # duplicate!

    errors_by_clip, cross_clip_violations = validate_omni_clip_manifest_batch(
        [clip1, clip2], repo_root
    )
    assert "DLG_BIRTA_SLEEP_01" in cross_clip_violations
    assert cross_clip_violations["DLG_BIRTA_SLEEP_01"] == {"CLIP_SC0001_01", "CLIP_SC0001_02"}


def test_valid_manifest_with_multiple_beats_per_shot(repo_root):
    """Shot can reference multiple source beats."""
    record = _minimal_omni_clip_manifest(total_duration_seconds=8)
    record["shots"] = [
        {
            "shot_id": "SHOT_SC0001_01_A",
            "duration_seconds": 8,
            "source_beat_ids": [
                "NADIA_PASSAGE_MOVEMENT",
                "WATER_GLASS_ACTION",
                "WRIST_SCAR_INSERT",
            ],
            "prompt_action": "Merged kitchen action",
            "duration_reason": "Three beats merged into one 8s shot",
        }
    ]
    errors = validate_omni_clip_manifest(record, repo_root)
    assert len(errors) == 0
