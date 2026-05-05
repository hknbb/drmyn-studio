"""
Build missing canonical asset work orders from pack lock readiness evidence.

This B7B agent is metadata-only. It turns readiness blockers into operator work
orders and never creates assets, mutates pack manifests, changes lock status, or
runs external generation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_AT = "2026-05-05T07:00:00Z"
DEFAULT_STORAGE_POLICY = "no_binary_commits"


class CanonicalAssetWorkOrderError(RuntimeError):
    """Raised when work orders cannot be built from repo metadata."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _asset_group_id(value: str) -> str:
    clean = "".join(char.lower() if char.isalnum() else "_" for char in value)
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean.strip("_") or "canonical_reference"


def _default_views(element_type: str) -> list[str]:
    if element_type == "character":
        return ["front_reference", "three_quarter_reference", "context_reference"]
    if element_type == "location":
        return ["wide_establishing", "threshold_or_route_geometry", "lighting_reference"]
    if element_type == "prop":
        return ["in_situ_context", "detail_closeup"]
    return ["canonical_reference"]


def _character_groups(intake: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in intake.get("wardrobe_image_groups") or []:
        if not isinstance(group, dict):
            continue
        wardrobe_id = _text(group.get("wardrobe_id")) or "wardrobe_context"
        groups.append(
            {
                "group_id": _asset_group_id(wardrobe_id),
                "group_type": "wardrobe_reference_set",
                "target_path": f"wardrobe/{wardrobe_id}/",
                "context": _text(group.get("context")),
                "required_views": _default_views("character"),
                "notes": _text(group.get("notes")),
                "source_status": _text(group.get("image_status")) or "not_collected",
            }
        )
    return groups


def _location_groups(intake: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in intake.get("sub_area_image_groups") or []:
        if not isinstance(group, dict):
            continue
        sub_area = _text(group.get("sub_area")) or "location_sub_area"
        groups.append(
            {
                "group_id": _asset_group_id(sub_area),
                "group_type": "location_sub_area_reference_set",
                "target_path": _text(group.get("target_path")) or f"sub_areas/{sub_area}/",
                "context": _text(group.get("visual_register")),
                "required_views": _default_views("location"),
                "notes": _text(group.get("notes")),
                "source_status": _text(group.get("image_status")) or "not_collected",
            }
        )
    return groups


def _prop_groups(intake: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = [
        str(item)
        for item in intake.get("image_requirements") or []
        if isinstance(item, str)
    ]
    return [
        {
            "group_id": "sc0001_canonical_prop_reference",
            "group_type": "prop_reference_set",
            "target_path": "canonical/",
            "context": _text(intake.get("canonical_name")) or _text(intake.get("element_id")),
            "required_views": _default_views("prop"),
            "notes": " | ".join(requirements),
            "source_status": "not_collected",
        }
    ]


def _fallback_groups(intake: dict[str, Any]) -> list[dict[str, Any]]:
    element_type = _text(intake.get("element_type")) or "unknown"
    return [
        {
            "group_id": "canonical_reference",
            "group_type": f"{element_type}_reference_set",
            "target_path": "canonical/",
            "context": _text(intake.get("canonical_name")) or _text(intake.get("element_id")),
            "required_views": _default_views(element_type),
            "notes": "No detailed image group structure was available in the intake manifest.",
            "source_status": "not_collected",
        }
    ]


def _required_asset_groups(intake: dict[str, Any]) -> list[dict[str, Any]]:
    element_type = _text(intake.get("element_type"))
    if element_type == "character":
        groups = _character_groups(intake)
    elif element_type == "location":
        groups = _location_groups(intake)
    elif element_type == "prop":
        groups = _prop_groups(intake)
    else:
        groups = []
    return groups or _fallback_groups(intake)


def _acceptance_checklist() -> list[str]:
    return [
        "Real canonical reference image assets are committed under the pack path.",
        "Committed image assets match the required asset groups and views.",
        "Image assets are tracked by the configured visual_dev/elements Git LFS rules.",
        "image_intake_manifest.yaml source_status is updated to source_images_in_repo.",
        "copyright_review is complete.",
        "provenance_review is complete.",
        "intake_ready_to_proceed is true.",
        "pack_manifest.yaml lists the relevant text assets and remains metadata_only until human lock review.",
    ]


def _work_order_from_pack(
    *,
    repo_root: Path,
    scene_id: str,
    index: int,
    pack: dict[str, Any],
) -> dict[str, Any]:
    intake_path_text = _text(pack.get("image_intake_manifest_ref"))
    intake_path = repo_root / intake_path_text
    intake = _read_yaml(intake_path)
    if not isinstance(intake, dict):
        intake = {}

    element_id = _text(intake.get("element_id")) or f"PACK{index:02d}"
    element_type = _text(intake.get("element_type")) or "unknown"
    pack_path = _text(pack.get("pack_path"))
    open_blockers = [
        str(item)
        for item in pack.get("open_blockers") or intake.get("open_blockers") or []
        if isinstance(item, str)
    ]

    return {
        "work_order_id": f"{scene_id}_ASSET_{index:02d}_{element_id}",
        "element_id": element_id,
        "element_type": element_type,
        "pack_path": pack_path,
        "source_pack_readiness": {
            "pack_manifest_ref": pack.get("pack_manifest_ref"),
            "image_intake_manifest_ref": intake_path_text,
            "source_notes_ref": pack.get("source_notes_ref"),
            "pack_status": pack.get("pack_status"),
            "canonical_asset_count": pack.get("canonical_asset_count"),
            "source_status": pack.get("source_status"),
            "copyright_review": pack.get("copyright_review"),
            "provenance_review": pack.get("provenance_review"),
            "intake_ready_to_proceed": pack.get("intake_ready_to_proceed"),
        },
        "required_asset_groups": _required_asset_groups(intake),
        "provenance_required": True,
        "copyright_required": True,
        "intake_ready_to_proceed_required": True,
        "lfs_required": True,
        "blocking_notes": open_blockers,
        "missing_requirements": pack.get("missing_requirements") or [],
        "acceptance_checklist": _acceptance_checklist(),
        "forbidden_actions": [
            "Do not change pack_status to locked in this work order.",
            "Do not fabricate placeholder binaries.",
            "Do not mark copyright or provenance complete without reviewed evidence.",
            "Do not run external generation from this metadata batch.",
        ],
    }


def build_canonical_asset_work_orders(
    repo_root: str | Path,
    scene_id: str,
    *,
    report_at: str = DEFAULT_REPORT_AT,
) -> dict[str, Any]:
    """Build a deterministic canonical asset work order report."""

    root = Path(repo_root)
    readiness_ref = f"evidence/pack_lock_readiness/{scene_id}_pack_lock_readiness.yaml"
    readiness_path = root / readiness_ref
    readiness = _read_yaml(readiness_path)
    if not isinstance(readiness, dict):
        raise CanonicalAssetWorkOrderError(f"Missing pack readiness report: {readiness_ref}")
    packs = readiness.get("packs")
    if not isinstance(packs, list):
        raise CanonicalAssetWorkOrderError(f"Invalid packs list in {readiness_ref}")

    work_orders = [
        _work_order_from_pack(
            repo_root=root,
            scene_id=scene_id,
            index=index,
            pack=pack,
        )
        for index, pack in enumerate(packs, start=1)
        if isinstance(pack, dict)
    ]
    return {
        "scene_id": scene_id,
        "report_at": report_at,
        "source_readiness_ref": readiness_ref,
        "report_status": "work_orders_open",
        "summary": {
            "total_work_orders": len(work_orders),
            "asset_creation_performed": False,
            "pack_locking_performed": False,
            "external_generation_performed": False,
            "packs_ready_for_lock_review": 0,
        },
        "work_orders": work_orders,
        "storage_policy": DEFAULT_STORAGE_POLICY,
        "canonical_assets_created": False,
        "pack_manifest_mutation_performed": False,
        "lock_action_performed": False,
        "external_generation_performed": False,
        "binary_outputs_created": False,
        "lifecycle_promotion_performed": False,
    }


def write_canonical_asset_work_orders(
    repo_root: str | Path,
    scene_id: str,
    *,
    output_path: str | Path | None = None,
    report_at: str = DEFAULT_REPORT_AT,
) -> Path:
    """Write missing canonical asset work orders for one scene."""

    root = Path(repo_root)
    report = build_canonical_asset_work_orders(root, scene_id, report_at=report_at)
    out_path = (
        Path(output_path)
        if output_path is not None
        else root
        / "evidence"
        / "canonical_asset_work_orders"
        / f"{scene_id}_asset_work_orders.yaml"
    )
    _write_yaml(out_path, report)
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--report-at", default=DEFAULT_REPORT_AT)
    args = parser.parse_args(argv)

    write_canonical_asset_work_orders(
        args.repo_root,
        args.scene_id,
        output_path=args.output_path,
        report_at=args.report_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
