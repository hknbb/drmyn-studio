"""
Metadata-only scene clip locking for Batch 9.

This agent locks the selected external video take into final scene-clip
metadata. It never copies or creates video/proxy binaries and never mutates
video_takes.yaml, scene cards, prompt records, or pack manifests.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


SCENE_CLIP_MAP_HEADER = [
    "scene_id",
    "selected_take",
    "prompt_id",
    "external_storage_ref",
    "platform_asset_ref",
    "local_proxy_ref",
    "repo_binary_committed",
    "lock_status",
]
VIDEO_BINARY_EXTENSIONS = {".mp4", ".mov", ".mkv", ".wav"}


class SceneClipLockingError(ValueError):
    """Raised when final clip locking would violate Batch 9 rules."""


@dataclass(frozen=True)
class SceneClipLockingResult:
    selected_take_path: Path
    scene_clip_map_path: Path


class SceneClipLockingAgent:
    """Write selected_take.yaml and scene_clip_map.csv metadata only."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def lock_scene_clip(
        self,
        *,
        scene_id: str,
        locked_by: str,
        locked_at: str | None = None,
    ) -> SceneClipLockingResult:
        if not locked_by:
            raise SceneClipLockingError("locked_by is required")
        locked_at = locked_at or datetime.now(UTC).replace(microsecond=0).isoformat()

        video_takes_path = (
            self.repo_root / "visual_dev" / "omni_sets" / scene_id / "video_takes.yaml"
        )
        if not video_takes_path.exists():
            raise SceneClipLockingError(f"video_takes.yaml not found for {scene_id}")
        before_video_takes = video_takes_path.read_text(encoding="utf-8")
        video_takes = yaml.safe_load(before_video_takes)
        if not isinstance(video_takes, dict):
            raise SceneClipLockingError("video_takes.yaml must be a mapping")

        selected_take_id = video_takes.get("selected_take")
        if not selected_take_id:
            raise SceneClipLockingError("video_takes.yaml has no selected_take")
        takes = video_takes.get("takes")
        if not isinstance(takes, list):
            raise SceneClipLockingError("video_takes.yaml takes must be a list")
        selected_takes = [
            take
            for take in takes
            if isinstance(take, dict) and take.get("status") == "selected"
        ]
        if len(selected_takes) != 1:
            raise SceneClipLockingError("video_takes.yaml must contain exactly one selected take")
        selected_take = selected_takes[0]
        if selected_take.get("take_id") != selected_take_id:
            raise SceneClipLockingError(
                "selected_take must match the take_id with status selected"
            )
        if selected_take.get("repo_binary_committed") is not False:
            raise SceneClipLockingError("selected take repo_binary_committed must be false")

        external_storage_ref = selected_take.get("external_storage_ref")
        if not isinstance(external_storage_ref, str) or not external_storage_ref.strip():
            raise SceneClipLockingError("selected take external_storage_ref is required")
        local_proxy_ref = selected_take.get("local_proxy_ref")
        if self._looks_like_binary_repo_path(local_proxy_ref):
            raise SceneClipLockingError("local_proxy_ref must not point to a repo video binary")

        payload = {
            "scene_id": scene_id,
            "selected_take": selected_take_id,
            "source_video_takes": self._relative(video_takes_path),
            "prompt_id": video_takes.get("prompt_id"),
            "platform_asset_ref": selected_take.get("platform_asset_ref"),
            "external_storage_ref": external_storage_ref.strip(),
            "local_proxy_ref": local_proxy_ref or None,
            "repo_binary_committed": False,
            "lock_status": "locked_metadata_only",
            "locked_by": locked_by,
            "locked_at": locked_at,
            "storage_policy": "external_video_only",
            "notes": "Final scene clip locked as metadata only; binary remains external.",
        }

        selected_take_path = (
            self.repo_root / "visual_dev" / "omni_sets" / scene_id / "selected_take.yaml"
        )
        self._write_yaml(selected_take_path, payload)

        scene_clip_map_path = self.repo_root / "evidence" / "scene_clip_map.csv"
        row = {
            "scene_id": scene_id,
            "selected_take": selected_take_id,
            "prompt_id": str(video_takes.get("prompt_id") or ""),
            "external_storage_ref": external_storage_ref.strip(),
            "platform_asset_ref": str(selected_take.get("platform_asset_ref") or ""),
            "local_proxy_ref": str(local_proxy_ref or ""),
            "repo_binary_committed": "false",
            "lock_status": "locked_metadata_only",
        }
        self._upsert_scene_clip_map(scene_clip_map_path, row)

        if video_takes_path.read_text(encoding="utf-8") != before_video_takes:
            raise SceneClipLockingError("video_takes.yaml was modified unexpectedly")

        return SceneClipLockingResult(
            selected_take_path=selected_take_path,
            scene_clip_map_path=scene_clip_map_path,
        )

    @staticmethod
    def _looks_like_binary_repo_path(value: Any) -> bool:
        if not value:
            return False
        text = str(value)
        if "://" in text:
            return False
        return Path(text).suffix.lower() in VIDEO_BINARY_EXTENSIONS

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @staticmethod
    def _upsert_scene_clip_map(path: Path, row: dict[str, str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, str]] = []
        if path.exists():
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != SCENE_CLIP_MAP_HEADER:
                    raise SceneClipLockingError("scene_clip_map.csv header is invalid")
                rows = list(reader)

        for existing in rows:
            if existing.get("scene_id") == row["scene_id"]:
                if existing == row:
                    return
                raise SceneClipLockingError(
                    f"scene_clip_map.csv already has a different row for {row['scene_id']}"
                )

        rows.append(row)
        rows.sort(key=lambda item: item["scene_id"])
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SCENE_CLIP_MAP_HEADER)
            writer.writeheader()
            writer.writerows(rows)
