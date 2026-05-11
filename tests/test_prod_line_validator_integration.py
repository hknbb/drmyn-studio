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


def test_new_directories_missing_still_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    report = run_validation(tmp_path, report_json=tmp_path / "report.json")
    assert report.total_files == 0
    assert report.invalid_files == 0
    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert payload["total_files"] == 0
