"""
Audit canonical reference asset readiness before pack locking.

This B7A audit is intentionally read-only with respect to element packs: it
reports missing canonical assets, provenance, copyright review, and manifest
evidence, but never writes pack_status or creates placeholder media.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_STORAGE_POLICY = "no_binary_commits"
DEFAULT_REPORT_AT = "2026-05-04T20:15:00Z"


class PackLockReadinessError(RuntimeError):
    """Raised when the readiness audit cannot be produced."""


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


def _lfs_tracking_configured(repo_root: Path) -> bool:
    gitattributes = repo_root / ".gitattributes"
    if not gitattributes.exists():
        return False
    text = gitattributes.read_text(encoding="utf-8")
    return all(
        pattern in text
        for pattern in (
            "visual_dev/elements/**/*.png",
            "visual_dev/elements/**/*.jpg",
            "visual_dev/elements/**/*.jpeg",
            "visual_dev/elements/**/*.webp",
        )
    )


def _canonical_asset_paths(repo_root: Path, pack_path: Path) -> list[str]:
    if not pack_path.is_dir():
        return []
    return [
        _relative(path, repo_root)
        for path in sorted(pack_path.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def _read_gate_pack_entries(repo_root: Path, scene_id: str) -> list[dict[str, Any]]:
    gate_path = repo_root / "evidence" / "omni_set_gates" / f"{scene_id}_gate.yaml"
    gate = _read_yaml(gate_path)
    if not isinstance(gate, dict):
        raise PackLockReadinessError(f"Missing Omni set gate report: {_relative(gate_path, repo_root)}")
    element_pack_gate = gate.get("element_pack_gate")
    if not isinstance(element_pack_gate, dict):
        raise PackLockReadinessError(f"Invalid Omni set gate report: {_relative(gate_path, repo_root)}")
    elements = element_pack_gate.get("elements")
    if not isinstance(elements, list):
        raise PackLockReadinessError(f"Invalid element_pack_gate.elements in {_relative(gate_path, repo_root)}")
    return [entry for entry in elements if isinstance(entry, dict)]


def _pack_readiness(
    *,
    repo_root: Path,
    gate_entry: dict[str, Any],
    lfs_ready: bool,
) -> dict[str, Any]:
    pack_path_text = _text(gate_entry.get("pack_path_expected"))
    pack_path = repo_root / pack_path_text if pack_path_text else repo_root / "__missing_pack__"
    pack_manifest_path = pack_path / "pack_manifest.yaml"
    intake_manifest_path = pack_path / "image_intake_manifest.yaml"
    source_notes_path = pack_path / "source_notes.md"

    pack_manifest = _read_yaml(pack_manifest_path)
    intake_manifest = _read_yaml(intake_manifest_path)
    source_notes_exists = source_notes_path.exists() and source_notes_path.stat().st_size > 0
    canonical_assets = _canonical_asset_paths(repo_root, pack_path)

    missing: list[str] = []
    pack_status = None
    if not isinstance(pack_manifest, dict):
        missing.append("pack_manifest.yaml missing")
    else:
        pack_status = pack_manifest.get("pack_status")
        if pack_status != "metadata_only":
            missing.append("pack_status is not metadata_only for pre-lock audit")
        text_assets = pack_manifest.get("text_assets")
        if not isinstance(text_assets, list) or "source_notes.md" not in text_assets:
            missing.append("pack_manifest.text_assets does not list source_notes.md")

    if not isinstance(intake_manifest, dict):
        missing.append("image_intake_manifest.yaml missing")
        intake_ready = False
        source_status = None
        copyright_review = None
        provenance_review = None
        open_blockers: list[str] = []
    else:
        intake_ready = intake_manifest.get("intake_ready_to_proceed") is True
        source_status = intake_manifest.get("source_status")
        copyright_review = intake_manifest.get("copyright_review")
        provenance_review = intake_manifest.get("provenance_review")
        open_blockers = [
            str(item)
            for item in intake_manifest.get("open_blockers", [])
            if isinstance(item, str)
        ]
        if not intake_ready:
            missing.append("image_intake_manifest.intake_ready_to_proceed is not true")
        if source_status != "source_images_in_repo":
            missing.append("source images are not present in repo")
        if copyright_review != "complete":
            missing.append("copyright_review is not complete")
        if provenance_review != "complete":
            missing.append("provenance_review is not complete")

    if not source_notes_exists:
        missing.append("source_notes.md missing or empty")
    if not canonical_assets:
        missing.append("no canonical image assets found in pack")
    if not lfs_ready:
        missing.append("Git LFS tracking for visual_dev/elements image assets is not configured")

    return {
        "element_ref": gate_entry.get("element_ref"),
        "pack_path": pack_path_text or None,
        "pack_manifest_ref": _relative(pack_manifest_path, repo_root),
        "image_intake_manifest_ref": _relative(intake_manifest_path, repo_root),
        "source_notes_ref": _relative(source_notes_path, repo_root),
        "pack_status": pack_status,
        "canonical_asset_count": len(canonical_assets),
        "canonical_assets": canonical_assets,
        "source_status": source_status,
        "copyright_review": copyright_review,
        "provenance_review": provenance_review,
        "intake_ready_to_proceed": intake_ready,
        "source_notes_present": source_notes_exists,
        "lfs_tracking_configured": lfs_ready,
        "ready_for_lock_review": not missing,
        "missing_requirements": missing,
        "open_blockers": open_blockers,
    }


def audit_pack_lock_readiness(
    repo_root: str | Path,
    scene_id: str,
    *,
    report_at: str = DEFAULT_REPORT_AT,
) -> dict[str, Any]:
    """Return a deterministic B7A pack lock readiness report for one scene."""

    root = Path(repo_root)
    lfs_ready = _lfs_tracking_configured(root)
    pack_entries = [
        _pack_readiness(repo_root=root, gate_entry=entry, lfs_ready=lfs_ready)
        for entry in _read_gate_pack_entries(root, scene_id)
    ]
    ready_count = sum(1 for entry in pack_entries if entry["ready_for_lock_review"])
    total = len(pack_entries)
    report_status = (
        "ready_for_human_lock_review"
        if total > 0 and ready_count == total
        else "blocked_missing_canonical_assets"
    )

    return {
        "scene_id": scene_id,
        "report_at": report_at,
        "source_gate_ref": f"evidence/omni_set_gates/{scene_id}_gate.yaml",
        "report_status": report_status,
        "ready_for_human_lock_review": report_status == "ready_for_human_lock_review",
        "summary": {
            "total_packs": total,
            "ready_for_lock_review": ready_count,
            "blocked_packs": total - ready_count,
            "packs_with_canonical_assets": sum(
                1 for entry in pack_entries if entry["canonical_asset_count"] > 0
            ),
            "packs_missing_canonical_assets": sum(
                1 for entry in pack_entries if entry["canonical_asset_count"] == 0
            ),
        },
        "pack_requirements": {
            "canonical_assets_required": True,
            "source_images_must_be_in_repo": True,
            "copyright_review_required": "complete",
            "provenance_review_required": "complete",
            "intake_ready_to_proceed_required": True,
            "lfs_tracking_required": True,
        },
        "packs": pack_entries,
        "lock_action_performed": False,
        "pack_manifest_mutation_performed": False,
        "canonical_assets_created": False,
        "external_generation_performed": False,
        "binary_outputs_created": False,
        "lifecycle_promotion_performed": False,
        "storage_policy": DEFAULT_STORAGE_POLICY,
    }


def write_pack_lock_readiness_report(
    repo_root: str | Path,
    scene_id: str,
    *,
    output_path: str | Path | None = None,
    report_at: str = DEFAULT_REPORT_AT,
) -> Path:
    """Write a metadata-only B7A pack lock readiness report."""

    root = Path(repo_root)
    report = audit_pack_lock_readiness(root, scene_id, report_at=report_at)
    out_path = (
        Path(output_path)
        if output_path is not None
        else root / "evidence" / "pack_lock_readiness" / f"{scene_id}_pack_lock_readiness.yaml"
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

    write_pack_lock_readiness_report(
        args.repo_root,
        args.scene_id,
        output_path=args.output_path,
        report_at=args.report_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
