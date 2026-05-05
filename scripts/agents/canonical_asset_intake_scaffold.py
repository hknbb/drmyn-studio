"""
Create metadata-only canonical asset intake scaffolding from B7B work orders.

This B7C agent creates directories, .gitkeep files, and intake_slot.yaml
metadata. It does not create reference assets, mutate pack manifests, lock
packs, complete provenance/copyright review, or run external generation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_AT = "2026-05-05T07:30:00Z"
DEFAULT_STORAGE_POLICY = "no_binary_commits"


class CanonicalAssetIntakeScaffoldError(RuntimeError):
    """Raised when intake scaffolding cannot be created from work orders."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _target_dir(repo_root: Path, pack_path: str, group_target_path: str) -> Path:
    return repo_root / pack_path / group_target_path


def _slot_payload(
    *,
    scene_id: str,
    work_order: dict[str, Any],
    group: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "work_order_id": work_order["work_order_id"],
        "element_id": work_order["element_id"],
        "element_type": work_order["element_type"],
        "group_id": group["group_id"],
        "group_type": group["group_type"],
        "context": group.get("context", ""),
        "required_views": group.get("required_views", []),
        "notes": group.get("notes", ""),
        "source_status": "not_collected",
        "copyright_review": "pending",
        "provenance_review": "pending",
        "intake_ready_to_proceed": False,
        "canonical_assets_committed": [],
        "storage_policy": DEFAULT_STORAGE_POLICY,
        "forbidden_actions": [
            "Do not add placeholder binaries.",
            "Do not mark copyright_review complete without reviewed evidence.",
            "Do not mark provenance_review complete without reviewed evidence.",
            "Do not change pack_status from this intake slot.",
            "Do not run external generation from this metadata scaffold.",
        ],
    }


def _readme_text(work_order: dict[str, Any], group: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {work_order['element_id']} {group['group_id']} intake slot",
            "",
            "Metadata-only canonical asset intake scaffold.",
            "",
            "Do not commit placeholder binaries here.",
            "Do not mark copyright or provenance complete without reviewed evidence.",
            "Do not change pack status from this folder.",
            "",
        ]
    )


def scaffold_canonical_asset_intake(
    repo_root: str | Path,
    scene_id: str,
    *,
    report_at: str = DEFAULT_REPORT_AT,
) -> dict[str, Any]:
    """Create intake slot folders and return a deterministic report."""

    root = Path(repo_root)
    work_orders_ref = (
        f"evidence/canonical_asset_work_orders/{scene_id}_asset_work_orders.yaml"
    )
    work_orders_path = root / work_orders_ref
    work_orders_doc = _read_yaml(work_orders_path)
    if not isinstance(work_orders_doc, dict):
        raise CanonicalAssetIntakeScaffoldError(
            f"Missing canonical asset work orders: {work_orders_ref}"
        )
    work_orders = work_orders_doc.get("work_orders")
    if not isinstance(work_orders, list):
        raise CanonicalAssetIntakeScaffoldError(
            f"Invalid work_orders list in {work_orders_ref}"
        )

    slots: list[dict[str, Any]] = []
    for work_order in work_orders:
        if not isinstance(work_order, dict):
            continue
        pack_path = str(work_order.get("pack_path") or "")
        groups = work_order.get("required_asset_groups") or []
        for group in groups:
            if not isinstance(group, dict):
                continue
            target_path = str(group.get("target_path") or "")
            slot_dir = _target_dir(root, pack_path, target_path)
            slot_yaml = slot_dir / "intake_slot.yaml"
            readme = slot_dir / "README.md"
            gitkeep = slot_dir / ".gitkeep"

            _write_yaml(
                slot_yaml,
                _slot_payload(scene_id=scene_id, work_order=work_order, group=group),
            )
            _write_text(readme, _readme_text(work_order, group))
            gitkeep.parent.mkdir(parents=True, exist_ok=True)
            gitkeep.touch()

            slots.append(
                {
                    "work_order_id": work_order["work_order_id"],
                    "element_id": work_order["element_id"],
                    "group_id": group["group_id"],
                    "slot_dir": _relative(slot_dir, root),
                    "intake_slot_ref": _relative(slot_yaml, root),
                    "readme_ref": _relative(readme, root),
                    "gitkeep_ref": _relative(gitkeep, root),
                    "source_status": "not_collected",
                    "copyright_review": "pending",
                    "provenance_review": "pending",
                    "intake_ready_to_proceed": False,
                    "canonical_assets_created": False,
                }
            )

    return {
        "scene_id": scene_id,
        "report_at": report_at,
        "source_work_orders_ref": work_orders_ref,
        "report_status": "intake_scaffold_created",
        "summary": {
            "total_slots": len(slots),
            "canonical_assets_created": False,
            "pack_locking_performed": False,
            "pack_manifest_mutation_performed": False,
            "external_generation_performed": False,
        },
        "slots": slots,
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


def write_canonical_asset_intake_scaffold(
    repo_root: str | Path,
    scene_id: str,
    *,
    output_path: str | Path | None = None,
    report_at: str = DEFAULT_REPORT_AT,
) -> Path:
    """Create intake slot folders and write the scaffold report."""

    root = Path(repo_root)
    report = scaffold_canonical_asset_intake(root, scene_id, report_at=report_at)
    out_path = (
        Path(output_path)
        if output_path is not None
        else root
        / "evidence"
        / "canonical_asset_intake_scaffolds"
        / f"{scene_id}_intake_scaffold.yaml"
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

    write_canonical_asset_intake_scaffold(
        args.repo_root,
        args.scene_id,
        output_path=args.output_path,
        report_at=args.report_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
