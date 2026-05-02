"""Read-only review metadata loaders for the copilot dashboard."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


IMAGE_SELECTION_PATTERN = "visual_dev/elements/**/image_selection.yaml"
VIDEO_TAKES_PATTERN = "visual_dev/omni_sets/SC*/video_takes.yaml"

REPO_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
REPO_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".wav"}


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_metadata(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None


def _repo_relative_status(ref: str, repo_root: Path) -> tuple[str, bool]:
    ref_path = Path(ref)
    if ref_path.is_absolute() or ".." in ref_path.parts:
        return "unsafe_path", False
    resolved = (repo_root / ref_path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return "unsafe_path", False
    return "repo_relative", resolved.exists()


def classify_media_ref(ref: object, repo_root: str | Path) -> dict[str, Any]:
    """Classify a media reference without opening, copying, or validating media bytes."""
    if ref is None:
        return {
            "ref": "",
            "kind": "none",
            "display_mode": "text",
            "exists_in_repo": False,
            "warning": "No media reference recorded.",
        }

    value = str(ref).strip()
    if not value:
        return {
            "ref": "",
            "kind": "none",
            "display_mode": "text",
            "exists_in_repo": False,
            "warning": "No media reference recorded.",
        }

    lowered = value.lower()
    if lowered.startswith("local://"):
        return {
            "ref": value,
            "kind": "local_manual",
            "display_mode": "text",
            "exists_in_repo": False,
            "warning": "Manual local storage reference; dashboard does not open it.",
        }
    if lowered.startswith("gdrive://"):
        return {
            "ref": value,
            "kind": "gdrive_manual",
            "display_mode": "text",
            "exists_in_repo": False,
            "warning": "Manual Google Drive reference; dashboard does not use Drive APIs.",
        }
    if "://" in lowered:
        return {
            "ref": value,
            "kind": "external",
            "display_mode": "text",
            "exists_in_repo": False,
            "warning": "External storage reference; dashboard renders text only.",
        }

    root = Path(repo_root)
    kind, exists = _repo_relative_status(value, root)
    suffix = Path(value).suffix.lower()
    if suffix in REPO_IMAGE_EXTENSIONS:
        media_kind = "image"
    elif suffix in REPO_VIDEO_EXTENSIONS:
        media_kind = "video"
    else:
        media_kind = "metadata"
    warning = (
        "Repo-relative reference; rendered as metadata only in this read-only panel."
        if kind == "repo_relative"
        else "Unsafe path reference; rendered as text only."
    )
    return {
        "ref": value,
        "kind": kind,
        "media_kind": media_kind,
        "display_mode": "text",
        "exists_in_repo": exists,
        "warning": warning,
    }


def _image_candidate_rows(
    *,
    payload: dict[str, Any],
    record_path: Path,
    repo_root: Path,
) -> list[dict[str, Any]]:
    candidates = payload.get("candidate_images")
    if not isinstance(candidates, list):
        return []

    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            continue
        path_ref = classify_media_ref(candidate.get("path"), repo_root)
        storage_ref = classify_media_ref(candidate.get("external_storage_ref"), repo_root)
        rows.append(
            {
                "record_path": _relative(record_path, repo_root),
                "element_id": str(payload.get("element_id") or ""),
                "element_type": str(payload.get("element_type") or ""),
                "round_status": str(payload.get("round_status") or ""),
                "candidate_index": index,
                "asset_id": str(candidate.get("asset_id") or ""),
                "status": str(candidate.get("status") or ""),
                "path_ref": path_ref["ref"],
                "path_kind": path_ref["kind"],
                "path_display": path_ref["display_mode"],
                "path_exists_in_repo": path_ref["exists_in_repo"],
                "external_storage_ref": storage_ref["ref"],
                "external_storage_kind": storage_ref["kind"],
                "reason": str(candidate.get("reason") or ""),
                "repo_binary_committed": bool(candidate.get("repo_binary_committed", False)),
                "warning": path_ref["warning"],
            }
        )
    return rows


def load_image_candidate_rows(
    repo_root: str | Path,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Load image candidate metadata rows from existing image_selection records."""
    root = Path(repo_root)
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob(IMAGE_SELECTION_PATTERN)):
        payload = _load_metadata(path)
        if not isinstance(payload, dict):
            continue
        rows.extend(
            _image_candidate_rows(
                payload=payload,
                record_path=path,
                repo_root=root,
            )
        )
        if len(rows) >= limit:
            return rows[:limit]
    return rows


def _video_take_rows(
    *,
    payload: dict[str, Any],
    record_path: Path,
    repo_root: Path,
) -> list[dict[str, Any]]:
    takes = payload.get("takes")
    if not isinstance(takes, list):
        return []

    rows: list[dict[str, Any]] = []
    for take in takes:
        if not isinstance(take, dict):
            continue
        external_ref = classify_media_ref(take.get("external_storage_ref"), repo_root)
        proxy_ref = classify_media_ref(take.get("local_proxy_ref"), repo_root)
        rows.append(
            {
                "record_path": _relative(record_path, repo_root),
                "scene_id": str(payload.get("scene_id") or ""),
                "prompt_id": str(payload.get("prompt_id") or ""),
                "round_status": str(payload.get("round_status") or ""),
                "selected_take": str(payload.get("selected_take") or ""),
                "take_id": str(take.get("take_id") or ""),
                "status": str(take.get("status") or ""),
                "storage_status": str(take.get("storage_status") or ""),
                "platform_asset_ref": str(take.get("platform_asset_ref") or ""),
                "external_storage_ref": external_ref["ref"],
                "external_storage_kind": external_ref["kind"],
                "local_proxy_ref": proxy_ref["ref"],
                "local_proxy_kind": proxy_ref["kind"],
                "local_proxy_display": proxy_ref["display_mode"],
                "local_proxy_exists_in_repo": proxy_ref["exists_in_repo"],
                "repo_binary_committed": bool(take.get("repo_binary_committed", False)),
                "reason": str(take.get("reason") or ""),
                "failure_reason": str(take.get("failure_reason") or ""),
                "warning": (
                    proxy_ref["warning"]
                    if proxy_ref["kind"] != "none"
                    else external_ref["warning"]
                ),
            }
        )
    return rows


def load_video_take_rows(
    repo_root: str | Path,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Load video take metadata rows from existing video_takes records."""
    root = Path(repo_root)
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob(VIDEO_TAKES_PATTERN)):
        payload = _load_metadata(path)
        if not isinstance(payload, dict):
            continue
        rows.extend(
            _video_take_rows(
                payload=payload,
                record_path=path,
                repo_root=root,
            )
        )
        if len(rows) >= limit:
            return rows[:limit]
    return rows


def load_review_panel_data(repo_root: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Load all read-only review panel rows."""
    return {
        "image_candidates": load_image_candidate_rows(repo_root),
        "video_takes": load_video_take_rows(repo_root),
    }
