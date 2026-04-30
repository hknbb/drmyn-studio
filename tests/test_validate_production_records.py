from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_production_records import main, run_validation  # noqa: E402


PROMPT_ID = "SC0003__t2i-char-c01-midjourney__v01"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _copy_schemas(repo_root: Path) -> None:
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True)
    for name in (
        "image_selection.schema.json",
        "asset_clearance.schema.json",
        "storyboard_option.schema.json",
        "shot_list_omni_suggestion.schema.json",
        "video_take.schema.json",
        "video_review.schema.json",
        "batch_job.schema.json",
        "operator_session.schema.json",
    ):
        (schemas_dir / name).write_text(
            (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _quality_scores() -> dict[str, int]:
    return {
        "identity_consistency": 4,
        "source_grounding": 5,
        "style_compliance": 4,
        "continuity": 4,
        "production_usability": 5,
    }


def _valid_image_selection() -> dict:
    return {
        "element_id": "C01",
        "element_type": "character",
        "selection_round": 1,
        "source_prompt_ids": [PROMPT_ID],
        "candidate_images": [
            {
                "asset_id": "C01_nadia_front_v01",
                "path": "visual_dev/elements/characters/C01/candidates/nadia_front_v01.png",
                "status": "selected",
                "reason": "Strong identity consistency and source grounding.",
                "quality_scores": _quality_scores(),
                "failure_reason": None,
                "repo_binary_committed": False,
            }
        ],
        "canonical_images": [
            "visual_dev/elements/characters/C01/candidates/nadia_front_v01.png"
        ],
        "round_status": "complete",
        "pack_manifest_sync": "pending",
    }


def _valid_asset_clearance() -> dict:
    return {
        "asset_id": "C01_nadia_front_v01",
        "element_id": "C01",
        "element_type": "character",
        "asset_path": "visual_dev/elements/characters/C01/candidates/nadia_front_v01.png",
        "source_prompt_id": PROMPT_ID,
        "source_model": "midjourney",
        "commercial_use_allowed": "pending_review",
        "actor_likeness_risk": False,
        "style_imitation_risk": False,
        "watermark_detected": False,
        "face_identity_drift": False,
        "review_notes": "Pending human clearance.",
        "clearance_status": "pending_review",
    }


def _valid_pack_suggestion() -> dict:
    return {
        "element_id": "C01",
        "suggested_field": "pack_status",
        "suggested_value": "seeded",
        "reason": "image_selection.yaml complete with canonical_images non-empty",
        "applied_by": None,
        "applied_at": None,
    }


def _valid_prompt_review_brief() -> dict:
    return {
        "source_prompt_id": PROMPT_ID,
        "corrected_brief": {
            "revision_reason": "Reduce editorial styling.",
            "negative_constraints": ["No fashion editorial lighting."],
        },
    }


def _valid_operator_session() -> dict:
    return {
        "session_id": "OP-SC0001-20260430",
        "created_at": "2026-04-30T00:00:00Z",
        "scene_id": "SC0001",
        "current_task": "t2i_image_generation",
        "recommended_files": ["prompts/draft/SC0001__t2i-char-c01-midjourney__v01.yaml"],
        "recommended_steps": ["Run external T2I generation manually."],
        "status": "planned",
        "notes": "Metadata-only operator session.",
    }


def test_empty_repo_paths_pass(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    report = run_validation(tmp_path)
    assert report.total_files == 0
    assert report.valid_files == 0
    assert report.invalid_files == 0
    assert not report.has_errors
    assert main(["--repo-root", str(tmp_path)]) == 0


def test_valid_image_selection_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/image_selection.yaml",
        _valid_image_selection(),
    )

    report = run_validation(tmp_path)

    assert report.total_files == 1
    assert report.valid_files == 1
    assert report.issues == []


def test_missing_quality_score_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_image_selection()
    payload["candidate_images"][0]["quality_scores"].pop("continuity")
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/image_selection.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any("continuity" in issue.message for issue in report.issues)


def test_invalid_failure_reason_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_image_selection()
    payload["candidate_images"][0]["status"] = "rejected"
    payload["candidate_images"][0]["failure_reason"] = "too_weird"
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/image_selection.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any("too_weird" in issue.message for issue in report.issues)


def test_valid_asset_clearance_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "evidence/asset_clearance/C01_nadia_front_v01.yaml",
        _valid_asset_clearance(),
    )

    report = run_validation(tmp_path)

    assert report.total_files == 1
    assert report.valid_files == 1
    assert report.issues == []


def test_invalid_commercial_use_allowed_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_asset_clearance()
    payload["commercial_use_allowed"] = "yes"
    _write_yaml(
        tmp_path / "evidence/asset_clearance/C01_nadia_front_v01.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any("commercial_use_allowed" in issue.field_path for issue in report.issues)


def test_pack_manifest_update_suggestion_missing_suggested_field_fails(
    tmp_path: Path,
) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_pack_suggestion()
    payload.pop("suggested_field")
    _write_yaml(
        tmp_path
        / "visual_dev/elements/characters/C01/pack_manifest_update_suggestion.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any(issue.field_path == "suggested_field" for issue in report.issues)


def test_prompt_review_corrected_brief_missing_source_prompt_id_fails(
    tmp_path: Path,
) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_prompt_review_brief()
    payload.pop("source_prompt_id")
    _write_yaml(
        tmp_path / "evidence/prompt_reviews/SC0003__t2i-char-c01-midjourney__v02_brief.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any(issue.field_path == "source_prompt_id" for issue in report.issues)


def test_report_json_is_written(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/image_selection.yaml",
        _valid_image_selection(),
    )
    report_path = tmp_path / "evidence/validation_reports/production_records.json"

    report = run_validation(tmp_path, report_json=report_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report.total_files == 1
    assert payload["total_files"] == 1
    assert payload["by_record_type"]["image_selection"] == 1


def test_valid_operator_session_passes(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    _write_yaml(
        tmp_path / "evidence/operator_sessions/OP-SC0001-20260430.yaml",
        _valid_operator_session(),
    )

    report = run_validation(tmp_path)

    assert report.total_files == 1
    assert report.valid_files == 1
    assert report.by_record_type["operator_session"] == 1
    assert report.issues == []


def test_invalid_operator_session_status_fails(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    payload = _valid_operator_session()
    payload["status"] = "promoted"
    _write_yaml(
        tmp_path / "evidence/operator_sessions/OP-SC0001-20260430.yaml",
        payload,
    )

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any(issue.record_type == "operator_session" for issue in report.issues)
