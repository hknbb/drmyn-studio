from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.canonical_asset_work_orders import (  # noqa: E402
    build_canonical_asset_work_orders,
    main as canonical_asset_work_orders_main,
    write_canonical_asset_work_orders,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_readiness(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "evidence/pack_lock_readiness/SC0001_pack_lock_readiness.yaml",
        {
            "scene_id": "SC0001",
            "packs": [
                {
                    "pack_path": "visual_dev/elements/characters/C01/",
                    "pack_manifest_ref": "visual_dev/elements/characters/C01/pack_manifest.yaml",
                    "image_intake_manifest_ref": "visual_dev/elements/characters/C01/image_intake_manifest.yaml",
                    "source_notes_ref": "visual_dev/elements/characters/C01/source_notes.md",
                    "pack_status": "metadata_only",
                    "canonical_asset_count": 0,
                    "source_status": "no_source_images_in_repo",
                    "copyright_review": "pending",
                    "provenance_review": "pending",
                    "intake_ready_to_proceed": False,
                    "missing_requirements": ["no canonical image assets found in pack"],
                    "open_blockers": ["Two wardrobe contexts require separate reference image sets."],
                }
            ],
        },
    )
    _write_yaml(
        tmp_path / "visual_dev/elements/characters/C01/image_intake_manifest.yaml",
        {
            "element_id": "C01",
            "element_type": "character",
            "wardrobe_image_groups": [
                {
                    "wardrobe_id": "WD001",
                    "context": "early morning",
                    "image_status": "not_collected",
                    "notes": "Muted domestic neutrals.",
                },
                {
                    "wardrobe_id": "WD002",
                    "context": "night private",
                    "image_status": "not_collected",
                    "notes": "Low-key night register.",
                },
            ],
            "open_blockers": [
                "Two wardrobe contexts require separate reference image sets."
            ],
        },
    )


def test_builds_character_work_order_from_readiness_and_intake(tmp_path: Path) -> None:
    _write_readiness(tmp_path)

    report = build_canonical_asset_work_orders(tmp_path, "SC0001")
    order = report["work_orders"][0]

    assert report["report_status"] == "work_orders_open"
    assert report["summary"]["total_work_orders"] == 1
    assert report["summary"]["asset_creation_performed"] is False
    assert report["canonical_assets_created"] is False
    assert report["lock_action_performed"] is False
    assert order["element_id"] == "C01"
    assert [group["group_id"] for group in order["required_asset_groups"]] == [
        "wd001",
        "wd002",
    ]
    assert order["provenance_required"] is True
    assert order["copyright_required"] is True
    assert "no canonical image assets found in pack" in order["missing_requirements"]


def test_cli_writes_schema_valid_work_order(tmp_path: Path) -> None:
    _write_readiness(tmp_path)

    code = canonical_asset_work_orders_main(
        [
            "--repo-root",
            str(tmp_path),
            "--scene-id",
            "SC0001",
        ]
    )
    report_path = tmp_path / "evidence/canonical_asset_work_orders/SC0001_asset_work_orders.yaml"
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (REPO_ROOT / "schemas/canonical_asset_work_order.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert code == 0
    assert report["binary_outputs_created"] is False
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_real_sc0001_work_orders_preserve_known_blockers() -> None:
    report = build_canonical_asset_work_orders(REPO_ROOT, "SC0001")

    assert report["summary"]["total_work_orders"] == 4
    assert report["canonical_assets_created"] is False
    assert report["pack_manifest_mutation_performed"] is False
    assert report["lock_action_performed"] is False

    orders = {order["element_id"]: order for order in report["work_orders"]}
    assert [group["group_id"] for group in orders["C01"]["required_asset_groups"]] == [
        "wd001",
        "wd002",
    ]
    assert "WD004 exact garment breakdown is unresolved" in " ".join(
        orders["C03"]["blocking_notes"]
    )
    assert [group["group_id"] for group in orders["LOC001"]["required_asset_groups"]] == [
        "kitchen_passage",
        "jins_room",
        "trophy_room",
    ]
    assert "copyright clearance decision" in " ".join(
        orders["PROP003"]["blocking_notes"]
    )
    assert all(
        "Do not change pack_status to locked in this work order."
        in order["forbidden_actions"]
        for order in orders.values()
    )


def test_real_sc0001_work_order_file_has_no_binary_side_effects(tmp_path: Path) -> None:
    output_path = tmp_path / "SC0001_asset_work_orders.yaml"

    write_canonical_asset_work_orders(
        REPO_ROOT,
        "SC0001",
        output_path=output_path,
        report_at="2026-05-05T07:00:00Z",
    )
    report = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert report["scene_id"] == "SC0001"
    assert report["storage_policy"] == "no_binary_commits"
    assert report["external_generation_performed"] is False
    assert report["binary_outputs_created"] is False
    assert not list(tmp_path.rglob("*.mp4"))
    assert not list(tmp_path.rglob("*.mov"))
