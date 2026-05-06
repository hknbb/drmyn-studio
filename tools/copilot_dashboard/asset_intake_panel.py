"""Asset intake readiness loader and local staging writer for the copilot dashboard."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


INTAKE_SLOT_PATTERN = "visual_dev/elements/**/intake_slot.yaml"

# B8A scope: only this slot is approved for first canonical asset intake.
FIRST_INTAKE_SLOT = ("C01", "wd001")

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


def _missing_views(required: list[str], committed: list[Any]) -> list[str]:
    committed_names = {Path(str(c)).stem.lower() for c in committed if c}
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
