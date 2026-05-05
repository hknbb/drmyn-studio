from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.canonical_asset_intake_instructions import (  # noqa: E402
    build_canonical_asset_intake_instructions,
    main as canonical_asset_intake_instructions_main,
    write_canonical_asset_intake_instructions,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_scaffold(tmp_path: Path) -> None:
    slot_ref = "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(
        tmp_path / "evidence/canonical_asset_intake_scaffolds/SC0001_intake_scaffold.yaml",
        {
            "scene_id": "SC0001",
            "slots": [
                {
                    "work_order_id": "SC0001_ASSET_01_C01",
                    "element_id": "C01",
                    "group_id": "wd001",
                    "slot_dir": "visual_dev/elements/characters/C01/wardrobe/WD001",
                    "intake_slot_ref": slot_ref,
                }
            ],
        },
    )
    _write_yaml(
        tmp_path / slot_ref,
        {
            "scene_id": "SC0001",
            "work_order_id": "SC0001_ASSET_01_C01",
            "element_id": "C01",
            "element_type": "character",
            "group_id": "wd001",
            "required_views": ["front_reference", "context_reference"],
            "source_status": "not_collected",
            "copyright_review": "pending",
            "provenance_review": "pending",
            "intake_ready_to_proceed": False,
            "canonical_assets_committed": [],
            "forbidden_actions": ["Do not add placeholder binaries."],
        },
    )


def test_builds_operator_instruction_without_asset_or_lock_claims(tmp_path: Path) -> None:
    _write_scaffold(tmp_path)

    report = build_canonical_asset_intake_instructions(tmp_path, "SC0001")
    instruction = report["instructions"][0]

    assert report["report_status"] == "human_intake_instructions_ready"
    assert report["summary"]["total_instructions"] == 1
    assert report["canonical_assets_created"] is False
    assert report["lock_action_performed"] is False
    assert instruction["required_asset_count"] == "2 images minimum, one per required view"
    assert "Place approved image files" in " ".join(instruction["operator_steps"])
    assert "copyright_review is complete" in " ".join(
        instruction["intake_ready_to_proceed_conditions"]
    )
    assert instruction["status_after_this_batch"]["source_status"] == "not_collected"


def test_cli_writes_schema_valid_instruction_record(tmp_path: Path) -> None:
    _write_scaffold(tmp_path)

    code = canonical_asset_intake_instructions_main(
        [
            "--repo-root",
            str(tmp_path),
            "--scene-id",
            "SC0001",
        ]
    )
    report_path = (
        tmp_path
        / "evidence/canonical_asset_intake_instructions/SC0001_intake_instructions.yaml"
    )
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (REPO_ROOT / "schemas/canonical_asset_intake_instruction.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert code == 0
    assert report["binary_outputs_created"] is False
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_real_sc0001_instructions_cover_all_slots_and_known_guidance() -> None:
    report = build_canonical_asset_intake_instructions(REPO_ROOT, "SC0001")
    instructions = {
        (instruction["element_id"], instruction["group_id"]): instruction
        for instruction in report["instructions"]
    }

    assert report["summary"]["total_instructions"] == 7
    assert ("C01", "wd001") in instructions
    assert ("C01", "wd002") in instructions
    assert ("C03", "wd004") in instructions
    assert ("LOC001", "kitchen_passage") in instructions
    assert ("LOC001", "jins_room") in instructions
    assert ("LOC001", "trophy_room") in instructions
    assert ("PROP003", "sc0001_canonical_prop_reference") in instructions
    assert "Keep sub-areas visually distinct" in " ".join(
        instructions[("LOC001", "kitchen_passage")]["prompt_guidance"]
    )
    assert "copyright decision" in " ".join(
        instructions[("PROP003", "sc0001_canonical_prop_reference")][
            "prompt_guidance"
        ]
    )
    assert all(
        instruction["status_after_this_batch"]["intake_ready_to_proceed"] is False
        for instruction in instructions.values()
    )


def test_real_sc0001_instruction_file_has_no_binary_side_effects(tmp_path: Path) -> None:
    output_path = tmp_path / "SC0001_intake_instructions.yaml"

    write_canonical_asset_intake_instructions(
        REPO_ROOT,
        "SC0001",
        output_path=output_path,
        report_at="2026-05-05T08:15:00Z",
    )
    report = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert report["scene_id"] == "SC0001"
    assert report["storage_policy"] == "no_binary_commits"
    assert report["canonical_assets_created"] is False
    assert report["pack_manifest_mutation_performed"] is False
    assert report["external_generation_performed"] is False
    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.mp4"))
