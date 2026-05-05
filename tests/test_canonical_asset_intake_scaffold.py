from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.canonical_asset_intake_scaffold import (  # noqa: E402
    scaffold_canonical_asset_intake,
    main as canonical_asset_intake_scaffold_main,
    write_canonical_asset_intake_scaffold,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_work_orders(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "evidence/canonical_asset_work_orders/SC0001_asset_work_orders.yaml",
        {
            "scene_id": "SC0001",
            "work_orders": [
                {
                    "work_order_id": "SC0001_ASSET_01_C01",
                    "element_id": "C01",
                    "element_type": "character",
                    "pack_path": "visual_dev/elements/characters/C01/",
                    "required_asset_groups": [
                        {
                            "group_id": "wd001",
                            "group_type": "wardrobe_reference_set",
                            "target_path": "wardrobe/WD001/",
                            "context": "early morning",
                            "required_views": ["front_reference"],
                            "notes": "Muted domestic neutrals.",
                            "source_status": "not_collected",
                        }
                    ],
                }
            ],
        },
    )


def test_scaffold_creates_slot_files_without_assets_or_locks(tmp_path: Path) -> None:
    _write_work_orders(tmp_path)

    report = scaffold_canonical_asset_intake(tmp_path, "SC0001")
    slot = report["slots"][0]
    slot_yaml = tmp_path / slot["intake_slot_ref"]
    slot_payload = yaml.safe_load(slot_yaml.read_text(encoding="utf-8"))

    assert report["summary"]["total_slots"] == 1
    assert report["canonical_assets_created"] is False
    assert report["lock_action_performed"] is False
    assert slot_payload["source_status"] == "not_collected"
    assert slot_payload["copyright_review"] == "pending"
    assert slot_payload["provenance_review"] == "pending"
    assert slot_payload["intake_ready_to_proceed"] is False
    assert (tmp_path / slot["readme_ref"]).exists()
    assert (tmp_path / slot["gitkeep_ref"]).exists()
    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("pack_manifest.yaml"))


def test_cli_writes_schema_valid_scaffold_report(tmp_path: Path) -> None:
    _write_work_orders(tmp_path)

    code = canonical_asset_intake_scaffold_main(
        [
            "--repo-root",
            str(tmp_path),
            "--scene-id",
            "SC0001",
        ]
    )
    report_path = (
        tmp_path
        / "evidence/canonical_asset_intake_scaffolds/SC0001_intake_scaffold.yaml"
    )
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (REPO_ROOT / "schemas/canonical_asset_intake_scaffold.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert code == 0
    assert report["binary_outputs_created"] is False
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_real_sc0001_scaffold_creates_expected_slots() -> None:
    report = scaffold_canonical_asset_intake(REPO_ROOT, "SC0001")
    slot_dirs = {slot["slot_dir"] for slot in report["slots"]}

    assert report["summary"]["total_slots"] == 7
    assert {
        "visual_dev/elements/characters/C01/wardrobe/WD001",
        "visual_dev/elements/characters/C01/wardrobe/WD002",
        "visual_dev/elements/characters/C03/wardrobe/WD004",
        "visual_dev/elements/locations/LOC001/sub_areas/kitchen_passage",
        "visual_dev/elements/locations/LOC001/sub_areas/jins_room",
        "visual_dev/elements/locations/LOC001/sub_areas/trophy_room",
        "visual_dev/elements/props/PROP003/canonical",
    } <= slot_dirs
    assert report["canonical_assets_created"] is False
    assert report["pack_manifest_mutation_performed"] is False
    assert report["copyright_completion_claimed"] is False
    assert report["provenance_completion_claimed"] is False


def test_real_sc0001_slot_metadata_remains_pending_and_binary_free(tmp_path: Path) -> None:
    output_path = tmp_path / "SC0001_intake_scaffold.yaml"

    write_canonical_asset_intake_scaffold(
        REPO_ROOT,
        "SC0001",
        output_path=output_path,
        report_at="2026-05-05T07:30:00Z",
    )
    report = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert report["scene_id"] == "SC0001"
    assert report["storage_policy"] == "no_binary_commits"
    assert report["external_generation_performed"] is False
    assert report["binary_outputs_created"] is False
    assert not list(tmp_path.rglob("*.mp4"))
    assert not list(tmp_path.rglob("*.mov"))
