from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validators.validate_shot_element_manifest import (  # noqa: E402
    validate_shot_element_manifest_file,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _copy_schema(repo_root: Path) -> None:
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True)
    for name in ("shot_element_manifest.schema.json",):
        (schemas_dir / name).write_text(
            (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _manifest(gate_status: str = "all_elements_ready") -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "shot_element_manifest",
        "manifest_id": "MANIFEST_SC0001_SH001_V001",
        "scene_id": "SC0001",
        "shot_id": "SH001",
        "required_elements": [
            {
                "element_id": "C01",
                "element_type": "character",
                "role": "primary_subject",
                "registration_state_required": "created",
            }
        ],
        "environmental_only_allowed_ids": [],
        "gate_status": gate_status,
    }


def _binding(status: str = "created") -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "element_binding",
        "element_id": "C01",
        "element_type": "character",
        "kling_alias": "@Nadia",
        "binding_status": status,
    }


def _kling_reference(status: str = "review") -> dict:
    return {
        "schema_version": "0.x-draft",
        "record_type": "kling_element_reference_record",
        "kling_element_reference_id": "KLING_REF_C01_V001",
        "status": status,
        "element_id": "C01",
        "element_type": "character",
        "source_midjourney_reference": {
            "reference_id": "MJ_ELEMENT_C01_HERO_LOCKED_V001",
            "prompt_id": "MJ_PROMPT_C01_HERO_LOCKED_V001",
        },
        "gpt_images_2_perspectives": {
            "rear_or_side": "GPTIMG2_C01_P01_REAR_V001",
            "three_quarter_left": "GPTIMG2_C01_P02_THREE_QUARTER_LEFT_V001",
            "right_profile_side": "GPTIMG2_C01_P03_RIGHT_PROFILE_V001",
            "left_profile_side": "GPTIMG2_C01_P04_LEFT_PROFILE_V001",
        },
        "continuity_anchors": ["identity", "wardrobe"],
        "approval_gate": {
            "all_perspectives_score_85_plus": True,
            "operator_approved": True,
            "operator_session_ref": "OP-TEST",
        },
        "downstream_use": ["kling_omni_3_shot_prompt"],
    }


def _write_ready_c01(repo_root: Path, *, binding_status: str = "created", ref_status: str = "review") -> Path:
    _copy_schema(repo_root)
    manifest_path = repo_root / "visual_dev" / "omni_sets" / "SC0001" / "shot_element_manifests" / "SH001.yaml"
    _write_yaml(manifest_path, _manifest())
    _write_yaml(
        repo_root / "visual_dev" / "omni_sets" / "SC0001" / "element_bindings.yaml",
        _binding(binding_status),
    )
    element_root = repo_root / "visual_dev" / "elements" / "characters" / "C01"
    _write_yaml(element_root / "pack_manifest.yaml", {"element_id": "C01"})
    _write_yaml(element_root / "gpt_images_perspective_pack.yaml", {"element_id": "C01"})
    _write_yaml(element_root / "kling_element_reference.yaml", _kling_reference(ref_status))
    return manifest_path


def test_ready_manifest_passes(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(tmp_path)

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert issues == []


def test_planned_binding_blocks_manifest(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(tmp_path, binding_status="planned")

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert any("binding_status is 'planned'" in issue.message for issue in issues)
    assert any("computed gate_status is 'blocked'" in issue.message for issue in issues)


def test_missing_kling_reference_blocks_manifest(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(tmp_path)
    (tmp_path / "visual_dev" / "elements" / "characters" / "C01" / "kling_element_reference.yaml").unlink()

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert any("kling_element_reference not found" in issue.message for issue in issues)


def test_draft_kling_reference_blocks_manifest(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(tmp_path, ref_status="draft")

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert any("expected review or better" in issue.message for issue in issues)


def test_schema_rejects_planned_registration_state(tmp_path: Path) -> None:
    _copy_schema(tmp_path)
    manifest = _manifest()
    manifest["required_elements"][0]["registration_state_required"] = "planned"
    manifest_path = tmp_path / "visual_dev" / "omni_sets" / "SC0001" / "shot_element_manifests" / "SH001.yaml"
    _write_yaml(manifest_path, manifest)

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert any("not one of" in issue.message for issue in issues)


def test_consistent_blocked_manifest_passes_silently(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(
        tmp_path, binding_status="planned", ref_status="draft"
    )
    manifest = _manifest(gate_status="blocked")
    _write_yaml(manifest_path, manifest)

    issues = validate_shot_element_manifest_file(manifest_path, tmp_path)

    assert issues == []


def test_consistent_blocked_manifest_reports_causes_when_requested(tmp_path: Path) -> None:
    manifest_path = _write_ready_c01(
        tmp_path, binding_status="planned", ref_status="draft"
    )
    manifest = _manifest(gate_status="blocked")
    _write_yaml(manifest_path, manifest)

    issues = validate_shot_element_manifest_file(
        manifest_path, tmp_path, report_causes=True
    )

    assert any("binding_status is 'planned'" in issue.message for issue in issues)
    assert any("expected review or better" in issue.message for issue in issues)
    assert not any("computed gate_status" in issue.message for issue in issues)


def test_schema_contains_no_lifecycle_keys() -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "shot_element_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    forbidden = {"pack_status", "canon_lock", "approved", "locked"}
    assert forbidden.isdisjoint(schema["properties"])
