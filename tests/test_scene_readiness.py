from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.scene_readiness import (  # noqa: E402
    compute_scene_readiness,
    render_report,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_yaml_multi(path: Path, docs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump_all(docs, sort_keys=False), encoding="utf-8")


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
        "continuity_anchors": ["identity"],
        "approval_gate": {
            "all_perspectives_score_85_plus": True,
            "operator_approved": True,
            "operator_session_ref": "OP-TEST",
        },
        "downstream_use": ["kling_omni_3_shot_prompt"],
    }


def _scaffold_c01(repo_root: Path, *, binding_status: str, ref_status: str) -> None:
    _write_yaml_multi(
        repo_root / "visual_dev" / "omni_sets" / "SC0001" / "element_bindings.yaml",
        [
            {
                "schema_version": "0.x-draft",
                "record_type": "element_binding",
                "element_id": "C01",
                "element_type": "character",
                "kling_alias": "@Nadia",
                "binding_status": binding_status,
            }
        ],
    )
    element_root = repo_root / "visual_dev" / "elements" / "characters" / "C01"
    _write_yaml(element_root / "pack_manifest.yaml", {"element_id": "C01"})
    _write_yaml(element_root / "gpt_images_perspective_pack.yaml", {"element_id": "C01"})
    _write_yaml(element_root / "kling_element_reference.yaml", _kling_reference(ref_status))


def _scaffold_manifest(repo_root: Path, *, gate_status: str = "all_elements_ready") -> Path:
    manifest_path = (
        repo_root
        / "visual_dev"
        / "omni_sets"
        / "SC0001"
        / "shot_element_manifests"
        / "SH001.yaml"
    )
    _write_yaml(
        manifest_path,
        {
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
        },
    )
    return manifest_path


def test_no_manifests_returns_empty_report_with_authoring_hint(tmp_path: Path) -> None:
    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")

    assert report.shots == []
    rendered = render_report(report)
    assert "No shot_element_manifests found" in rendered
    assert "Next step: author" in rendered


def test_ready_scene_reports_all_elements_ready(tmp_path: Path) -> None:
    _scaffold_c01(tmp_path, binding_status="created", ref_status="review")
    _scaffold_manifest(tmp_path, gate_status="all_elements_ready")

    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")

    assert len(report.shots) == 1
    shot = report.shots[0]
    assert shot.declared_gate_status == "all_elements_ready"
    assert shot.computed_gate_status == "all_elements_ready"
    assert len(shot.elements) == 1
    element = shot.elements[0]
    assert element.is_ready is True
    assert element.blockers == []
    assert element.next_steps == []
    rendered = render_report(report)
    assert "[READY] C01" in rendered
    assert "0 blocking" in rendered


def test_planned_binding_surfaces_blocker_and_next_step(tmp_path: Path) -> None:
    _scaffold_c01(tmp_path, binding_status="planned", ref_status="review")
    _scaffold_manifest(tmp_path, gate_status="blocked")

    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")

    element = report.shots[0].elements[0]
    assert element.is_ready is False
    assert any("planned" in blocker for blocker in element.blockers)
    assert any(
        "promote element_binding.binding_status from planned -> created"
        in step
        for step in element.next_steps
    )


def test_draft_kling_reference_surfaces_blocker_and_next_step(tmp_path: Path) -> None:
    _scaffold_c01(tmp_path, binding_status="created", ref_status="draft")
    _scaffold_manifest(tmp_path, gate_status="blocked")

    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")

    element = report.shots[0].elements[0]
    assert element.is_ready is False
    assert any(
        "kling_element_reference.status is 'draft'" in blocker
        for blocker in element.blockers
    )
    assert any(
        "promote kling_element_reference.status from draft -> review" in step
        for step in element.next_steps
    )


def test_missing_pipeline_files_are_reported(tmp_path: Path) -> None:
    _scaffold_c01(tmp_path, binding_status="created", ref_status="review")
    (tmp_path / "visual_dev" / "elements" / "characters" / "C01" / "pack_manifest.yaml").unlink()
    (
        tmp_path
        / "visual_dev"
        / "elements"
        / "characters"
        / "C01"
        / "gpt_images_perspective_pack.yaml"
    ).unlink()
    _scaffold_manifest(tmp_path, gate_status="blocked")

    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")

    element = report.shots[0].elements[0]
    assert element.pack_manifest_present is False
    assert element.gpt_pack_present is False
    assert any("pack_manifest.yaml missing" in blocker for blocker in element.blockers)
    assert any(
        "gpt_images_perspective_pack.yaml missing" in blocker
        for blocker in element.blockers
    )


def test_json_render_is_parseable(tmp_path: Path) -> None:
    _scaffold_c01(tmp_path, binding_status="created", ref_status="review")
    _scaffold_manifest(tmp_path, gate_status="all_elements_ready")

    report = compute_scene_readiness(repo_root=tmp_path, scene_id="SC0001")
    payload = json.loads(render_report(report, fmt="json"))

    assert payload["scene_id"] == "SC0001"
    assert payload["shots"][0]["elements"][0]["is_ready"] is True
