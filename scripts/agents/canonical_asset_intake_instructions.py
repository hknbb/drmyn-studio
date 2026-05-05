"""
Build human-facing canonical asset intake instructions from B7C scaffold slots.

This B7D agent is metadata-only. It writes operator checklists and never creates
assets, changes pack manifests, completes copyright/provenance, locks packs, or
runs external generation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_AT = "2026-05-05T08:15:00Z"
DEFAULT_STORAGE_POLICY = "no_binary_commits"
DEFAULT_GUIDANCE_REF = "evidence/canonical_asset_work_orders/SC0001_asset_work_orders.yaml"


class CanonicalAssetIntakeInstructionError(RuntimeError):
    """Raised when instruction records cannot be built."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)


def _asset_count(required_views: list[Any]) -> str:
    count = len(required_views)
    if count <= 1:
        return "1 image minimum"
    return f"{count} images minimum, one per required view"


def _prompt_guidance(slot: dict[str, Any]) -> list[str]:
    element_type = slot.get("element_type")
    if element_type == "character":
        return [
            "Use the planning character record and source_notes.md for silhouette, wardrobe, and restraint.",
            "Do not invent styling beyond the slot context.",
            "Keep identity/name details out of downstream model prompts unless the prompt adapter explicitly permits them.",
        ]
    if element_type == "location":
        return [
            "Use the planning location record, source_notes.md, and slot context for architecture and light.",
            "Keep sub-areas visually distinct; do not merge kitchen_passage, jins_room, and trophy_room registers.",
            "Do not introduce ungrounded decor or genre exaggeration.",
        ]
    if element_type == "prop":
        return [
            "Use the planning prop record, source_notes.md, and slot notes for the required physical cue.",
            "For PROP003, resolve the Vardova skyline image copyright decision before intake can proceed.",
            "Do not imply recurrence beyond SC0001 unless the planning source changes.",
        ]
    return ["Use the work order and source notes as the acquisition authority."]


def _instruction_from_slot(repo_root: Path, slot: dict[str, Any]) -> dict[str, Any]:
    slot_ref = slot.get("intake_slot_ref")
    slot_payload = _read_yaml(repo_root / str(slot_ref))
    if not isinstance(slot_payload, dict):
        raise CanonicalAssetIntakeInstructionError(f"Missing intake slot: {slot_ref}")

    required_views = slot_payload.get("required_views") or []
    target_dir = slot.get("slot_dir")
    return {
        "instruction_id": f"{slot_payload['work_order_id']}_{slot_payload['group_id']}_INTAKE",
        "work_order_id": slot_payload["work_order_id"],
        "element_id": slot_payload["element_id"],
        "element_type": slot_payload["element_type"],
        "group_id": slot_payload["group_id"],
        "target_dir": target_dir,
        "intake_slot_ref": slot_ref,
        "required_asset_count": _asset_count(required_views),
        "required_views": required_views,
        "guidance_sources": [
            DEFAULT_GUIDANCE_REF,
            str(slot_ref),
            f"{target_dir}/README.md",
        ],
        "prompt_guidance": _prompt_guidance(slot_payload),
        "operator_steps": [
            f"Acquire or create real canonical reference image assets for {slot_payload['group_id']}.",
            f"Place approved image files under {target_dir}.",
            "Record provenance source, rights holder or generation source, and acquisition timestamp.",
            "Complete copyright review before changing copyright_review from pending.",
            "Complete provenance review before changing provenance_review from pending.",
            "Update canonical_assets_committed only with real image paths committed to the pack.",
        ],
        "intake_ready_to_proceed_conditions": [
            "At least one real canonical asset exists for every required view.",
            "All listed assets are in the slot target directory.",
            "Assets are covered by visual_dev/elements Git LFS tracking rules.",
            "source_status is source_images_in_repo.",
            "copyright_review is complete.",
            "provenance_review is complete.",
            "canonical_assets_committed lists the committed asset paths.",
        ],
        "forbidden_actions": slot_payload.get("forbidden_actions", []),
        "status_after_this_batch": {
            "source_status": slot_payload.get("source_status"),
            "copyright_review": slot_payload.get("copyright_review"),
            "provenance_review": slot_payload.get("provenance_review"),
            "intake_ready_to_proceed": slot_payload.get("intake_ready_to_proceed"),
            "canonical_assets_committed": slot_payload.get("canonical_assets_committed"),
        },
    }


def build_canonical_asset_intake_instructions(
    repo_root: str | Path,
    scene_id: str,
    *,
    report_at: str = DEFAULT_REPORT_AT,
) -> dict[str, Any]:
    """Return deterministic human-facing intake instructions."""

    root = Path(repo_root)
    scaffold_ref = (
        f"evidence/canonical_asset_intake_scaffolds/{scene_id}_intake_scaffold.yaml"
    )
    scaffold = _read_yaml(root / scaffold_ref)
    if not isinstance(scaffold, dict):
        raise CanonicalAssetIntakeInstructionError(f"Missing intake scaffold: {scaffold_ref}")
    slots = scaffold.get("slots")
    if not isinstance(slots, list):
        raise CanonicalAssetIntakeInstructionError(f"Invalid slots list in {scaffold_ref}")
    instructions = [
        _instruction_from_slot(root, slot)
        for slot in slots
        if isinstance(slot, dict)
    ]
    return {
        "scene_id": scene_id,
        "report_at": report_at,
        "source_intake_scaffold_ref": scaffold_ref,
        "report_status": "human_intake_instructions_ready",
        "summary": {
            "total_instructions": len(instructions),
            "canonical_assets_created": False,
            "pack_locking_performed": False,
            "pack_manifest_mutation_performed": False,
            "external_generation_performed": False,
        },
        "instructions": instructions,
        "storage_policy": DEFAULT_STORAGE_POLICY,
        "canonical_assets_created": False,
        "pack_manifest_mutation_performed": False,
        "lock_action_performed": False,
        "copyright_completion_claimed": False,
        "provenance_completion_claimed": False,
        "external_generation_performed": False,
        "binary_outputs_created": False,
        "lifecycle_promotion_performed": False,
    }


def write_canonical_asset_intake_instructions(
    repo_root: str | Path,
    scene_id: str,
    *,
    output_path: str | Path | None = None,
    report_at: str = DEFAULT_REPORT_AT,
) -> Path:
    """Write human-facing canonical asset intake instructions."""

    root = Path(repo_root)
    report = build_canonical_asset_intake_instructions(
        root,
        scene_id,
        report_at=report_at,
    )
    out_path = (
        Path(output_path)
        if output_path is not None
        else root
        / "evidence"
        / "canonical_asset_intake_instructions"
        / f"{scene_id}_intake_instructions.yaml"
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

    write_canonical_asset_intake_instructions(
        args.repo_root,
        args.scene_id,
        output_path=args.output_path,
        report_at=args.report_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
