from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_production_records import collect_production_files, run_validation  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _copy_schemas(repo_root: Path) -> None:
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "image_selection.schema.json",
        "asset_clearance.schema.json",
        "storyboard_option.schema.json",
        "shot_list_omni_suggestion.schema.json",
        "batch_job.schema.json",
        "operator_session.schema.json",
        "pre_b8a_clean_reset.schema.json",
        "gpt_images_perspective_pack.schema.json",
        "kling_element_reference_record.schema.json",
        "kling_shot_prompt_record.schema.json",
        "dialogue_extract_record.schema.json",
        "performance_intent_record.schema.json",
        "voice_binding_record.schema.json",
        "native_audio_compatibility_record.schema.json",
        "production_batch.schema.json",
    ):
        (schemas_dir / name).write_text(
            (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _valid_gpt_images_perspective_pack() -> dict:
    perspectives = [
        "front_hero",
        "three_quarter_left",
        "three_quarter_right",
        "rear_or_side",
    ]
    prompts = []
    for idx, perspective in enumerate(perspectives, start=1):
        prompts.append(
            {
                "prompt_id": f"SC0001__gpt-pack-{idx:02d}__v01",
                "perspective": perspective,
                "prompt_text": f"Render {perspective} preserving identity anchors.",
                "constraints": ["preserve facial structure", "preserve wardrobe colors"],
                "expected_output": {"asset_type": "still", "aspect_ratio": "1:1"},
            }
        )
    return {
        "schema_version": "0.x-draft",
        "record_type": "gpt_images_perspective_pack",
        "prompt_pack_id": "SC0001_GPTPACK_01",
        "status": "draft",
        "source_reference_id": "MJ_REF_SC0001_C01_HERO",
        "target_model": "gpt_images_2",
        "target_role": "multi_perspective_element_expander",
        "element_id": "C01",
        "element_type": "character",
        "shared_preservation_instruction": "Keep face topology and silhouette consistent.",
        "prompts": prompts,
        "qc_gate": {
            "minimum_score": 85,
            "all_perspectives_required": True,
            "failed_perspective_revision_only": True,
        },
        "downstream_use": ["kling_omni_3_shot_prompt"],
    }


def _valid_kling_shot_prompt_record(*, repo_binary_committed: bool = False) -> dict:
    payload = {
        "schema_version": "0.x-draft",
        "record_type": "kling_shot_prompt_record",
        "kling_shot_prompt_id": "KSP_SC0001_01_A_SAFE_V01",
        "status": "draft",
        "scene_id": "SC0001",
        "shot_id": "SHOT_SC0001_01_A",
        "linked_element_refs": ["KER_SC0001_C01_V01"],
        "duration_seconds": 5,
        "aspect_ratio": "16:9",
        "variant_mode": "safe",
        "render_pass": "visual_test",
        "quality_tier": "test_720p",
        "native_audio": False,
        "camera_plan": {
            "framing": "medium",
            "movement": "tracking",
            "lens_feel": "natural",
        },
        "action_timeline": ["enters frame", "stops at sink", "settles"],
        "constraints": ["no identity drift"],
        "materialized_output": {
            "platform": "kling",
            "external_storage_ref": "gdrive://kling/sc0001/shot-a-v01.mp4",
            "platform_job_id": "job_abc123",
            "repo_binary_committed": repo_binary_committed,
        },
    }
    return payload


def _valid_production_batch() -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "production_batch",
        "production_batch_id": "PB_SC0001_SEQ01_V01",
        "status": "draft",
        "scope": {"sequence_id": "SEQ01", "scenes": ["SC0001"]},
        "models": ["midjourney_v8_1", "gpt_images_2", "kling_omni_3"],
        "estimated_outputs": {
            "midjourney_images": 4,
            "gpt_images_perspectives": 4,
            "kling_video_takes": 3,
        },
        "retry_policy": {"max_retries_per_prompt": 2, "failure_reason_required": True},
        "cost_tracking": {"enabled": True, "estimated_budget": 25.0, "currency": "USD"},
    }


def _valid_kling_element_reference_record() -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "kling_element_reference_record",
        "kling_element_reference_id": "KER_SC0001_C01_V01",
        "status": "draft",
        "element_id": "C01",
        "element_type": "character",
        "source_midjourney_reference": {
            "reference_id": "MJ_REF_SC0001_C01_HERO",
            "prompt_id": "SC0001__mj-c01-hero__v01",
        },
        "gpt_images_2_perspectives": {
            "front_hero": "SC0001__gpt-pack-01__v01",
            "three_quarter_left": "SC0001__gpt-pack-02__v01",
            "three_quarter_right": "SC0001__gpt-pack-03__v01",
            "rear_or_side": "SC0001__gpt-pack-04__v01",
        },
        "continuity_anchors": ["face topology", "wardrobe silhouette"],
        "approval_gate": {
            "all_perspectives_score_85_plus": True,
            "operator_approved": False,
            "operator_session_ref": "OP-SC0001-001",
        },
        "downstream_use": ["kling_omni_3_shot_prompt"],
    }


def _valid_dialogue_extract_record() -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "dialogue_extract_record",
        "dialogue_extract_id": "DLG_SC0001_01",
        "status": "draft",
        "scene_id": "SC0001",
        "source_screenplay_span": {"start_line": 10, "end_line": 15},
        "speakers": [{"character_id": "C01", "display_name": "Nadia"}],
        "raw_lines": [{"speaker": "Nadia", "text": "I remember this place."}],
        "dialogue_function": "reveal memory trigger",
        "emotional_subtext": "contained anxiety",
        "target_language": "en",
        "language_support_status": "officially_supported",
    }


def _valid_performance_intent_record() -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "performance_intent_record",
        "performance_intent_id": "PERF_SC0001_01",
        "status": "draft",
        "scene_id": "SC0001",
        "shot_id": "SHOT_SC0001_01_A",
        "speaker": "Nadia",
        "spoken_line": "I remember this place.",
        "language": "en",
        "delivery": {
            "volume": "low",
            "pace": "measured",
            "tone": "dry",
            "emotional_state": "guarded",
        },
        "subtext": "concealing fear",
        "face_direction": "toward sink",
        "mouth_behavior": "controlled articulation",
    }


def _valid_voice_binding_record(*, binding_status: str = "prebound") -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "voice_binding_record",
        "voice_binding_id": "VOICE_SC0001_C01_V01",
        "status": "review",
        "character_id": "C01",
        "binding_status": binding_status,
        "binding_method": "prompt_described",
        "visual_reference_pack": "KER_SC0001_C01_V01",
        "language": "en",
        "operator_approved": False,
        "asset_clearance_ref": "evidence/asset_clearance/C01_nadia_front_v01.yaml",
    }


def _valid_native_audio_compatibility_record(
    *, compatible: bool = True, status: str = "review"
) -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "native_audio_compatibility_record",
        "native_audio_compatibility_id": "NAC_SC0001_01",
        "status": status,
        "scene_id": "SC0001",
        "shot_id": "SHOT_SC0001_01_A",
        "native_audio": True,
        "uses_video_input": False,
        "uses_image_or_element_refs": True,
        "compatible": compatible,
        "checked_against_snapshot": "model_guidance_snapshots/kling/20260508T140000Z_kling_omni_video_best_available.yaml",
    }


def test_collect_production_files_includes_prod_line_types(tmp_path: Path) -> None:
    files = collect_production_files(tmp_path)
    for record_type in (
        "gpt_images_perspective_pack",
        "kling_element_reference_record",
        "kling_shot_prompt_record",
        "dialogue_extract_record",
        "performance_intent_record",
        "voice_binding_record",
        "native_audio_compatibility_record",
        "production_batch",
    ):
        assert record_type in files
        assert files[record_type] == []


def test_valid_gpt_images_perspective_pack_validates(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path
        / "visual_dev/elements/characters/C01/gpt_images_perspective_pack.yaml",
        _valid_gpt_images_perspective_pack(),
    )
    report = run_validation(tmp_path)
    assert report.total_files == 1
    assert report.invalid_files == 0
    assert report.by_record_type["gpt_images_perspective_pack"] == 1


def test_kling_shot_prompt_repo_binary_committed_false_enforced(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/omni_sets/SC0001/kling_shot_prompt_001.yaml",
        _valid_kling_shot_prompt_record(repo_binary_committed=True),
    )
    report = run_validation(tmp_path)
    assert report.invalid_files == 1
    assert any(
        issue.record_type == "kling_shot_prompt_record"
        and "repo_binary_committed" in issue.field_path
        for issue in report.issues
    )


def test_production_batch_not_double_counted_as_batch_job(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "evidence/batch_jobs/production_batch_sc0001.yaml",
        _valid_production_batch(),
    )
    report = run_validation(tmp_path)
    assert report.by_record_type["production_batch"] == 1
    assert report.by_record_type["batch_job"] == 0
    assert report.invalid_files == 0


def test_production_batch_record_type_detected_without_filename_prefix(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "evidence/batch_jobs/PB_SC0001_SEQ01_V01.yaml",
        _valid_production_batch(),
    )
    grouped = collect_production_files(tmp_path)
    assert len(grouped["production_batch"]) == 1
    assert len(grouped["batch_job"]) == 0

    report = run_validation(tmp_path)
    assert report.by_record_type["production_batch"] == 1
    assert report.by_record_type["batch_job"] == 0
    assert report.invalid_files == 0


def test_new_directories_missing_still_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    report = run_validation(tmp_path, report_json=tmp_path / "report.json")
    assert report.total_files == 0
    assert report.invalid_files == 0
    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert payload["total_files"] == 0


def test_valid_minimal_prod_line_chain_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/gpt_images_perspective_pack.yaml",
        _valid_gpt_images_perspective_pack(),
    )
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/kling_element_reference.yaml",
        _valid_kling_element_reference_record(),
    )
    _write_yaml(
        tmp_path / "visual_dev/omni_sets/SC0001/kling_shot_prompt_001.yaml",
        _valid_kling_shot_prompt_record(),
    )
    report = run_validation(tmp_path)
    assert report.invalid_files == 0


def test_missing_kling_element_reference_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    shot = _valid_kling_shot_prompt_record()
    shot["linked_element_refs"] = ["KLING_REF_MISSING"]
    _write_yaml(tmp_path / "visual_dev/omni_sets/SC0001/kling_shot_prompt_001.yaml", shot)
    report = run_validation(tmp_path)
    assert any(
        i.record_type == "kling_shot_prompt_record"
        and i.field_path == "linked_element_refs"
        and "missing linked Kling element reference" in i.message
        for i in report.issues
    )


def test_missing_gpt_images_perspective_prompt_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/gpt_images_perspective_pack.yaml",
        _valid_gpt_images_perspective_pack(),
    )
    ker = _valid_kling_element_reference_record()
    ker["gpt_images_2_perspectives"]["rear_or_side"] = "SC0001__gpt-pack-99__v01"
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/kling_element_reference.yaml",
        ker,
    )
    report = run_validation(tmp_path)
    assert any(
        i.record_type == "kling_element_reference_record"
        and i.field_path == "gpt_images_2_perspectives"
        and "missing GPT Images 2 perspective prompt" in i.message
        for i in report.issues
    )


def test_native_audio_requires_dialogue_extract_and_performance_intent(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/gpt_images_perspective_pack.yaml",
        _valid_gpt_images_perspective_pack(),
    )
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/kling_element_reference.yaml",
        _valid_kling_element_reference_record(),
    )
    shot = _valid_kling_shot_prompt_record()
    shot["native_audio"] = True
    shot["dialogue"] = ["DLG_SC0001_01", "PERF_SC0001_01"]
    shot["speech_constraints"] = ["single speaker only"]
    shot["native_audio_compatibility"] = "NAC_SC0001_01"
    shot["voice_binding"] = "VOICE_SC0001_C01_V01"
    _write_yaml(tmp_path / "visual_dev/omni_sets/SC0001/kling_shot_prompt_001.yaml", shot)
    report = run_validation(tmp_path)
    assert any(
        i.record_type == "kling_shot_prompt_record"
        and i.field_path == "dialogue"
        and "missing dialogue extract/performance intent reference" in i.message
        for i in report.issues
    )


def test_pending_voice_binding_blocks_dialogue_shot(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/gpt_images_perspective_pack.yaml",
        _valid_gpt_images_perspective_pack(),
    )
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/kling_element_reference.yaml",
        _valid_kling_element_reference_record(),
    )
    _write_yaml(tmp_path / "planning/dialogue/DLG_SC0001_01.yaml", _valid_dialogue_extract_record())
    _write_yaml(
        tmp_path / "planning/dialogue/PERF_SC0001_01.yaml",
        _valid_performance_intent_record(),
    )
    _write_yaml(
        tmp_path / "planning/dialogue/VOICE_SC0001_C01_V01.yaml",
        _valid_voice_binding_record(binding_status="pending"),
    )
    _write_yaml(
        tmp_path / "evidence/native_audio_compatibility/NAC_SC0001_01.yaml",
        _valid_native_audio_compatibility_record(compatible=True, status="review"),
    )
    shot = _valid_kling_shot_prompt_record()
    shot["native_audio"] = True
    shot["dialogue"] = ["DLG_SC0001_01", "PERF_SC0001_01"]
    shot["speech_constraints"] = ["single speaker only"]
    shot["native_audio_compatibility"] = "NAC_SC0001_01"
    shot["voice_binding"] = "VOICE_SC0001_C01_V01"
    _write_yaml(tmp_path / "visual_dev/omni_sets/SC0001/kling_shot_prompt_001.yaml", shot)
    report = run_validation(tmp_path)
    assert any(
        i.record_type == "kling_shot_prompt_record"
        and i.field_path == "voice_binding"
        and "voice binding is pending and blocks dialogue shot production" in i.message
        for i in report.issues
    )


def test_incompatible_native_audio_must_be_blocked(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "evidence/native_audio_compatibility/NAC_SC0001_01.yaml",
        _valid_native_audio_compatibility_record(compatible=False, status="review"),
    )
    report = run_validation(tmp_path)
    assert any(
        i.record_type == "native_audio_compatibility_record"
        and i.field_path == "status"
        and "must use blocked status" in i.message
        for i in report.issues
    )
