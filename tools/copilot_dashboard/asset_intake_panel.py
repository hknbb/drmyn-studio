"""Asset intake readiness, staging, and preview helpers for the copilot dashboard."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


INTAKE_SLOT_PATTERN = "visual_dev/elements/**/intake_slot.yaml"

# B8A scope: only this slot is approved for first canonical asset intake.
FIRST_INTAKE_SLOT = ("C01", "wd001")
FIRST_INTAKE_SLOT_REF = "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"

# Staging area is gitignored — no canonical directory writes allowed.
STAGING_DIR_REL = "visual_dev/intake_staging/C01_WD001"

ALLOWED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})

VIEW_ROLE_OPTIONS = [
    "front_reference",
    "three_quarter_reference",
    "back_reference",
    "context_reference",
    "detail_reference",
    "other",
]


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_yaml(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


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


def _missing_views(required: list[str], committed: list[Any]) -> list[str]:
    missing = []
    for view in required:
        view_stem = view.lower().replace("_reference", "").replace("_", "")
        matched = any(view_stem in Path(str(c)).stem.lower() for c in committed if c)
        if not matched:
            missing.append(view)
    return missing


def _sanitize_filename(name: str) -> str:
    name = Path(name).name  # strip any path components including ../
    name = name.lower().replace(" ", "_")
    name = re.sub(r"[^\w.\-]", "", name)
    return name


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


@dataclass
class StagingResult:
    success: bool
    staged_path: str
    sidecar_path: str
    message: str


def stage_uploaded_file(
    repo_root: str | Path,
    file_bytes: bytes,
    original_filename: str,
    view_role: str,
    operator_note: str = "",
) -> StagingResult:
    """Write uploaded file to gitignored staging area. No canonical dir writes."""
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        return StagingResult(False, "", "", f"Rejected: unsupported type '{suffix}'")

    safe_name = _sanitize_filename(original_filename)
    if not safe_name or safe_name.startswith("."):
        return StagingResult(False, "", "", "Rejected: invalid filename after sanitization")

    root = Path(repo_root)
    staging_dir = root / STAGING_DIR_REL
    staging_dir.mkdir(parents=True, exist_ok=True)

    staged = staging_dir / safe_name
    staged.write_bytes(file_bytes)

    sidecar_data = {
        "target_slot_ref": "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml",
        "element_id": "C01",
        "group_id": "WD001",
        "view_role": view_role,
        "original_filename": original_filename,
        "staged_path": _relative(staged, root),
        "source_type": "human_uploaded_reference",
        "copyright_review": "pending",
        "provenance_review": "pending",
        "operator_note": operator_note,
    }
    sidecar = staging_dir / f"{safe_name}.sidecar.yaml"
    sidecar.write_text(yaml.safe_dump(sidecar_data, sort_keys=False), encoding="utf-8")

    return StagingResult(
        True,
        _relative(staged, root),
        _relative(sidecar, root),
        f"Staged: {safe_name}",
    )


def load_placement_preview(repo_root: str | Path) -> dict[str, Any]:
    """Load read-only staging placement preview data for B8-6C."""
    root = Path(repo_root)
    staging_dir = root / STAGING_DIR_REL
    slot_path = root / FIRST_INTAKE_SLOT_REF
    slot_payload = _load_yaml(slot_path)

    required_views: list[str] = []
    committed: list[Any] = []
    if isinstance(slot_payload, dict):
        required_views = list(slot_payload.get("required_views") or [])
        committed = list(slot_payload.get("canonical_assets_committed") or [])

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    preview_targets: list[str] = []

    if staging_dir.exists():
        staged_files = [
            path
            for path in sorted(staging_dir.iterdir())
            if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_SUFFIXES
        ]
        for staged in staged_files:
            staged_rel = _relative(staged, root)
            sidecar_path = staged.parent / f"{staged.name}.sidecar.yaml"
            sidecar = _load_yaml(sidecar_path)

            row_warnings: list[str] = []
            view_role = ""
            target_slot_ref = ""
            element_id = ""
            group_id = ""
            original_filename = ""

            if not sidecar_path.exists():
                row_warnings.append("Missing sidecar YAML.")
            elif not isinstance(sidecar, dict):
                row_warnings.append("Unreadable sidecar YAML.")
            else:
                view_role = str(sidecar.get("view_role") or "")
                target_slot_ref = str(sidecar.get("target_slot_ref") or "")
                element_id = str(sidecar.get("element_id") or "")
                group_id = str(sidecar.get("group_id") or "")
                original_filename = str(sidecar.get("original_filename") or "")
                sidecar_staged_path = str(sidecar.get("staged_path") or "")
                if sidecar_staged_path and sidecar_staged_path != staged_rel:
                    row_warnings.append(
                        "Sidecar staged_path does not match staged file location."
                    )
                target_slot_path = _safe_repo_relative_path(target_slot_ref, root)
                if target_slot_path is None:
                    row_warnings.append("Unsafe target slot ref.")
                elif target_slot_ref != FIRST_INTAKE_SLOT_REF:
                    row_warnings.append("Unsafe target slot ref outside approved B8A scope.")

            target_canonical_path = _preview_target_path(
                repo_root=root,
                target_slot_ref=target_slot_ref,
                element_id=element_id,
                group_id=group_id,
                view_role=view_role,
                suffix=staged.suffix,
            )
            if not target_canonical_path:
                row_warnings.append("Target canonical path unavailable.")
            else:
                preview_targets.append(target_canonical_path)
                if target_canonical_path in committed:
                    row_warnings.append(
                        "Target canonical path already exists in canonical_assets_committed."
                    )

            if view_role and required_views and view_role not in required_views:
                row_warnings.append("View role is not in required_views for the intake slot.")

            rows.append(
                {
                    "staged_path": staged_rel,
                    "sidecar_path": (
                        _relative(sidecar_path, root) if sidecar_path.exists() else ""
                    ),
                    "original_filename": original_filename or staged.name,
                    "view_role": view_role,
                    "target_slot_ref": target_slot_ref,
                    "target_canonical_path": target_canonical_path,
                    "warning": " | ".join(row_warnings) if row_warnings else "",
                }
            )

    target_counts: dict[str, int] = {}
    for target in preview_targets:
        target_counts[target] = target_counts.get(target, 0) + 1
    duplicate_targets = sorted(
        target for target, count in target_counts.items() if count > 1
    )
    if duplicate_targets:
        warnings.extend(
            f"Duplicate preview target path: {target}" for target in duplicate_targets
        )
        for row in rows:
            if row["target_canonical_path"] in duplicate_targets:
                extra = "Duplicate preview target path."
                row["warning"] = f"{row['warning']} | {extra}".strip(" |")

    orphan_sidecars: list[str] = []
    if staging_dir.exists():
        for sidecar_path in sorted(staging_dir.glob("*.sidecar.yaml")):
            staged_name = sidecar_path.name.removesuffix(".sidecar.yaml")
            if not (staging_dir / staged_name).exists():
                orphan_sidecars.append(_relative(sidecar_path, root))
    warnings.extend(f"Orphan sidecar without staged file: {path}" for path in orphan_sidecars)

    missing_now = _missing_views(required_views, committed)
    missing_after_preview = _missing_views(required_views, committed + preview_targets)

    return {
        "slot_path": _relative(slot_path, root),
        "slot_exists": slot_path.exists(),
        "staging_dir": _relative(staging_dir, root),
        "required_views": required_views,
        "committed_count": len(committed),
        "staged_count": len(rows),
        "missing_views_now": missing_now,
        "missing_views_after_preview": missing_after_preview,
        "duplicate_targets": duplicate_targets,
        "warnings": warnings,
        "rows": rows,
        "git_lfs_reminder": (
            "Canonical reference images under visual_dev/elements/** must be human-reviewed "
            "and Git LFS tracked before any human placement PR."
        ),
    }


def load_intake_slot_rows(repo_root: str | Path) -> list[dict[str, Any]]:
    """Load intake slot metadata rows. Read-only — no files are written or mutated."""
    root = Path(repo_root)
    rows: list[dict[str, Any]] = []

    for path in sorted(root.glob(INTAKE_SLOT_PATTERN)):
        payload = _load_yaml(path)
        if not isinstance(payload, dict):
            continue

        element_id = str(payload.get("element_id") or "")
        group_id = str(payload.get("group_id") or "")
        required_views: list[str] = payload.get("required_views") or []
        committed: list[Any] = payload.get("canonical_assets_committed") or []
        missing = _missing_views(required_views, committed)

        is_first_intake = (
            element_id.upper() == FIRST_INTAKE_SLOT[0].upper()
            and group_id.lower() == FIRST_INTAKE_SLOT[1].lower()
        )

        rows.append(
            {
                "slot_path": _relative(path, root),
                "element_id": element_id,
                "group_id": group_id,
                "element_type": str(payload.get("element_type") or ""),
                "group_type": str(payload.get("group_type") or ""),
                "scene_id": str(payload.get("scene_id") or ""),
                "context": str(payload.get("context") or ""),
                "source_status": str(payload.get("source_status") or ""),
                "storage_policy": str(payload.get("storage_policy") or ""),
                "copyright_review": str(payload.get("copyright_review") or ""),
                "provenance_review": str(payload.get("provenance_review") or ""),
                "intake_ready_to_proceed": bool(
                    payload.get("intake_ready_to_proceed", False)
                ),
                "required_views": ", ".join(required_views),
                "committed_count": len(committed),
                "missing_views": ", ".join(missing) if missing else "—",
                "is_first_intake_slot": is_first_intake,
            }
        )

    return rows
