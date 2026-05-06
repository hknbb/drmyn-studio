"""
Build a metadata-only clean reset audit before starting B8A.

The audit scans local staging and the approved WD001 canonical slot to confirm
that B8A can start from a clean branch and a clean asset state. It never deletes,
moves, copies, or mutates files under visual_dev/elements/**.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


DEFAULT_AUDIT_AT = "2026-05-06T14:30:00Z"
DEFAULT_SCENE_ID = "SC0001"
STAGING_ROOT_REL = Path("visual_dev/intake_staging")
APPROVED_STAGING_DIR_REL = Path("visual_dev/intake_staging/C01_WD001")
TARGET_SLOT_DIR_REL = Path("visual_dev/elements/characters/C01/wardrobe/WD001")
TARGET_SLOT_REF = "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
OUTPUT_REL = Path(
    "evidence/pre_b8a_clean_resets/SC0001_pre_b8a_clean_reset.yaml"
)
ALLOWED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
EXPECTED_CANONICAL_FILES = {".gitkeep", "README.md", "intake_slot.yaml"}
EXPECTED_SOURCE_STATUS = "not_collected"
EXPECTED_STORAGE_POLICY = "no_binary_commits"


class PreB8ACleanResetError(RuntimeError):
    """Raised when the clean reset audit cannot be built."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_repo_relative_path(ref: str, repo_root: Path) -> Path | None:
    candidate = Path(str(ref).strip())
    if not str(ref).strip() or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _canonical_view_token(view_role: str) -> str:
    token = str(view_role or "").strip().lower()
    token = token.replace("_reference", "")
    token = re.sub(r"[^\w]+", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "unassigned"


def _preview_target_path(
    *,
    repo_root: Path,
    target_slot_ref: str,
    element_id: str,
    group_id: str,
    view_role: str,
    suffix: str,
) -> str:
    target_slot = _safe_repo_relative_path(target_slot_ref, repo_root)
    if target_slot is None:
        return ""
    filename = (
        f"{str(element_id).lower()}_{str(group_id).lower()}_"
        f"{_canonical_view_token(view_role)}{suffix.lower()}"
    )
    return _relative(target_slot.parent / filename, repo_root)


def _load_slot_state(repo_root: Path) -> dict[str, Any]:
    slot_path = repo_root / TARGET_SLOT_REF
    slot = _read_yaml(slot_path)
    if not isinstance(slot, dict):
        raise PreB8ACleanResetError(f"Missing or invalid intake slot: {slot_path}")
    committed = slot.get("canonical_assets_committed") or []
    if not isinstance(committed, list):
        committed = []
    return {
        "slot_path": TARGET_SLOT_REF,
        "source_status": str(slot.get("source_status") or ""),
        "storage_policy": str(slot.get("storage_policy") or ""),
        "canonical_assets_committed_count": len(committed),
        "intake_ready_to_proceed": bool(slot.get("intake_ready_to_proceed", False)),
        "copyright_review": str(slot.get("copyright_review") or ""),
        "provenance_review": str(slot.get("provenance_review") or ""),
        "canonical_assets_committed": [str(ref) for ref in committed if ref],
    }


def build_pre_b8a_clean_reset(
    repo_root: str | Path,
    *,
    scene_id: str = DEFAULT_SCENE_ID,
    audit_at: str = DEFAULT_AUDIT_AT,
) -> dict[str, Any]:
    """Return the deterministic pre-B8A clean reset audit."""

    root = Path(repo_root)
    staging_root = root / STAGING_ROOT_REL
    approved_staging_dir = root / APPROVED_STAGING_DIR_REL
    canonical_dir = root / TARGET_SLOT_DIR_REL
    slot_state = _load_slot_state(root)

    all_staging_files = (
        sorted(path for path in staging_root.rglob("*") if path.is_file())
        if staging_root.exists()
        else []
    )
    approved_staging_files = (
        sorted(path for path in approved_staging_dir.iterdir() if path.is_file())
        if approved_staging_dir.exists()
        else []
    )

    staged_images = [
        path for path in approved_staging_files if path.suffix.lower() in ALLOWED_IMAGE_SUFFIXES
    ]
    all_staged_images = [
        path for path in all_staging_files if path.suffix.lower() in ALLOWED_IMAGE_SUFFIXES
    ]
    sidecar_files = [
        path for path in all_staging_files if path.name.endswith(".sidecar.yaml")
    ]
    unexpected_staging_paths = [
        _relative(path, root)
        for path in approved_staging_files
        if path not in staged_images and path not in sidecar_files
    ]

    staged_files_outside_wd001 = [
        _relative(path, root)
        for path in all_staging_files
        if approved_staging_dir not in path.parents
    ]

    orphan_sidecars: list[str] = []
    unsafe_paths: list[str] = []
    duplicate_target_candidates: list[str] = []
    target_counts: dict[str, int] = {}
    staged_images_without_sidecars: list[str] = []

    for sidecar_path in sidecar_files:
        staged_name = sidecar_path.name.removesuffix(".sidecar.yaml")
        staged_image_path = sidecar_path.with_name(staged_name)
        if not staged_image_path.exists():
            orphan_sidecars.append(_relative(sidecar_path, root))
            continue

        sidecar = _read_yaml(sidecar_path)
        if not isinstance(sidecar, dict):
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: unreadable sidecar YAML"
            )
            continue

        target_slot_ref = str(sidecar.get("target_slot_ref") or "")
        staged_path_ref = str(sidecar.get("staged_path") or "")
        if target_slot_ref != TARGET_SLOT_REF:
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: target_slot_ref={target_slot_ref}"
            )
        if _safe_repo_relative_path(target_slot_ref, root) is None:
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: unsafe target_slot_ref"
            )
        if _safe_repo_relative_path(staged_path_ref, root) is None:
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: unsafe staged_path"
            )
        elif staged_path_ref != _relative(staged_image_path, root):
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: staged_path mismatch"
            )

        target = _preview_target_path(
            repo_root=root,
            target_slot_ref=target_slot_ref,
            element_id=str(sidecar.get("element_id") or ""),
            group_id=str(sidecar.get("group_id") or ""),
            view_role=str(sidecar.get("view_role") or ""),
            suffix=staged_image_path.suffix,
        )
        if target:
            duplicate_target_candidates.append(target)
            target_counts[target] = target_counts.get(target, 0) + 1
        else:
            unsafe_paths.append(
                f"{_relative(sidecar_path, root)}: could not derive target canonical path"
            )

    for staged_image in all_staged_images:
        sidecar_path = staged_image.parent / f"{staged_image.name}.sidecar.yaml"
        if not sidecar_path.exists():
            staged_images_without_sidecars.append(_relative(staged_image, root))

    duplicate_target_canonical_paths = sorted(
        target for target, count in target_counts.items() if count > 1
    )

    unexpected_canonical_files = []
    if canonical_dir.exists():
        for path in sorted(canonical_dir.iterdir()):
            if path.name in EXPECTED_CANONICAL_FILES:
                continue
            unexpected_canonical_files.append(_relative(path, root))

    slot_baseline_clean = (
        slot_state["source_status"] == EXPECTED_SOURCE_STATUS
        and slot_state["storage_policy"] == EXPECTED_STORAGE_POLICY
        and slot_state["canonical_assets_committed_count"] == 0
        and slot_state["intake_ready_to_proceed"] is False
    )

    unexpected_staging_files_found = bool(
        all_staged_images or sidecar_files or unexpected_staging_paths
    )
    unsafe_paths_found = bool(unsafe_paths)
    duplicate_targets_found = bool(duplicate_target_canonical_paths)
    non_wd001_staging_found = bool(staged_files_outside_wd001)
    canonical_slot_unexpected_files_found = bool(
        unexpected_canonical_files or slot_state["canonical_assets_committed_count"] > 0
    )

    ready_for_b8a_clean_branch = not any(
        [
            unexpected_staging_files_found,
            orphan_sidecars,
            staged_images_without_sidecars,
            duplicate_targets_found,
            unsafe_paths_found,
            non_wd001_staging_found,
            canonical_slot_unexpected_files_found,
            not slot_baseline_clean,
        ]
    )

    reset_status = (
        "clean_for_b8a_start"
        if ready_for_b8a_clean_branch
        else "cleanup_required_before_b8a"
    )

    return {
        "scene_id": scene_id,
        "audit_at": audit_at,
        "target_slot": f"{TARGET_SLOT_DIR_REL.as_posix()}/",
        "reset_status": reset_status,
        "ready_for_b8a_clean_branch": ready_for_b8a_clean_branch,
        "staging_scan_complete": True,
        "unexpected_staging_files_found": unexpected_staging_files_found,
        "unsafe_paths_found": unsafe_paths_found,
        "duplicate_targets_found": duplicate_targets_found,
        "non_wd001_staging_found": non_wd001_staging_found,
        "canonical_slot_unexpected_files_found": canonical_slot_unexpected_files_found,
        "scan_roots": {
            "staging_root": STAGING_ROOT_REL.as_posix(),
            "approved_staging_dir": APPROVED_STAGING_DIR_REL.as_posix(),
            "target_slot_dir": TARGET_SLOT_DIR_REL.as_posix(),
            "target_slot_ref": TARGET_SLOT_REF,
        },
        "staged_files_count": len(all_staged_images),
        "sidecar_files_count": len(sidecar_files),
        "orphan_sidecars": orphan_sidecars,
        "staged_images_without_sidecars": staged_images_without_sidecars,
        "duplicate_target_canonical_paths": duplicate_target_canonical_paths,
        "unsafe_paths": sorted(set(unsafe_paths)),
        "staged_files_outside_wd001": staged_files_outside_wd001,
        "unexpected_staging_paths": unexpected_staging_paths,
        "unexpected_canonical_files": unexpected_canonical_files,
        "wd001_slot_state": {
            "slot_path": slot_state["slot_path"],
            "source_status": slot_state["source_status"],
            "storage_policy": slot_state["storage_policy"],
            "canonical_assets_committed_count": slot_state[
                "canonical_assets_committed_count"
            ],
            "intake_ready_to_proceed": slot_state["intake_ready_to_proceed"],
            "copyright_review": slot_state["copyright_review"],
            "provenance_review": slot_state["provenance_review"],
        },
        "deleted_files": False,
        "moved_files": False,
        "copied_files": False,
        "wrote_canonical_assets": False,
        "mutated_intake_slot": False,
        "updated_canonical_assets_committed": False,
        "changed_storage_policy": False,
        "approved_copyright": False,
        "approved_provenance": False,
        "set_intake_ready_to_proceed": False,
        "pack_locking_performed": False,
        "kling_generation_performed": False,
        "lifecycle_promotion_performed": False,
        "binaries_added": False,
    }


def write_pre_b8a_clean_reset(
    repo_root: str | Path,
    *,
    scene_id: str = DEFAULT_SCENE_ID,
    output_path: str | Path | None = None,
    audit_at: str = DEFAULT_AUDIT_AT,
) -> Path:
    """Write the pre-B8A clean reset record."""

    root = Path(repo_root)
    report = build_pre_b8a_clean_reset(root, scene_id=scene_id, audit_at=audit_at)
    out_path = Path(output_path) if output_path is not None else root / OUTPUT_REL
    _write_yaml(out_path, report)
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--scene-id", default=DEFAULT_SCENE_ID)
    parser.add_argument("--output-path")
    parser.add_argument("--audit-at", default=DEFAULT_AUDIT_AT)
    args = parser.parse_args(argv)

    write_pre_b8a_clean_reset(
        args.repo_root,
        scene_id=args.scene_id,
        output_path=args.output_path,
        audit_at=args.audit_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
