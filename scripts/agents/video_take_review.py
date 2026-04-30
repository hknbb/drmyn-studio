"""
Metadata-only Kling video take review for Batch 8.5.

This agent records externally generated take metadata and human review notes.
It never reads, copies, or creates video binaries; it also never writes
selected_take.yaml, scene_clip_map.csv, scene cards, prompt records, or pack
manifests.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.agents.review_outputs import FAILURE_REASONS, QUALITY_SCORE_FIELDS


TAKE_STATUSES = {
    "candidate",
    "rejected",
    "selected",
    "needs_revision",
    "deprecated",
}
STORAGE_STATUSES = {"stored_external", "pending_external"}
PROMPT_VERSION_RE = re.compile(r"^(?P<stem>SC\d{4}__[a-z0-9\-]+)__v(?P<version>\d{2})$")
VIDEO_BINARY_EXTENSIONS = {".mp4", ".mov", ".mkv", ".wav"}


class VideoTakeReviewError(ValueError):
    """Raised when video take metadata would violate Batch 8.5 rules."""


@dataclass(frozen=True)
class VideoTakeReviewResult:
    video_takes_path: Path
    review_path: Path
    corrected_brief_path: Path | None


class VideoTakeReviewAgent:
    """Write video take and review records without touching video binaries."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def write_review(
        self,
        *,
        scene_id: str,
        prompt_id: str,
        takes_metadata_path: str | Path,
        review_notes_path: str | Path,
    ) -> VideoTakeReviewResult:
        metadata_path = (self.repo_root / takes_metadata_path).resolve()
        notes_path = (self.repo_root / review_notes_path).resolve()
        if not metadata_path.exists():
            raise VideoTakeReviewError(f"Takes metadata not found: {takes_metadata_path}")
        if not notes_path.exists():
            raise VideoTakeReviewError(f"Review notes not found: {review_notes_path}")
        if metadata_path.suffix.lower() in VIDEO_BINARY_EXTENSIONS:
            raise VideoTakeReviewError("takes_metadata must be YAML or JSON, not a video binary")

        raw_metadata = self._load_metadata(metadata_path)
        raw_takes = self._extract_takes(raw_metadata)
        if not raw_takes:
            raise VideoTakeReviewError("takes metadata must include at least one take")

        takes = [self._normalize_take(take) for take in raw_takes]
        selected_take = self._selected_take_id(takes, raw_metadata)
        needs_prompt_revision = self._needs_prompt_revision(
            takes=takes,
            raw_metadata=raw_metadata,
            selected_take=selected_take,
        )
        round_status = "complete" if selected_take and not needs_prompt_revision else "needs_prompt_revision"
        review_notes = notes_path.read_text(encoding="utf-8")

        video_takes = {
            "scene_id": scene_id,
            "prompt_id": prompt_id,
            "takes": takes,
            "selected_take": selected_take,
            "round_status": round_status,
            "needs_prompt_revision": needs_prompt_revision,
            "storage_policy": "external_video_only",
        }
        video_takes_path = (
            self.repo_root / "visual_dev" / "omni_sets" / scene_id / "video_takes.yaml"
        )
        self._write_yaml(video_takes_path, video_takes)

        review_path = self.repo_root / "evidence" / "video_reviews" / f"{scene_id}_take_review.yaml"
        review_payload = {
            "scene_id": scene_id,
            "prompt_id": prompt_id,
            "review_notes_path": self._relative(notes_path),
            "review_notes": review_notes,
            "take_ids": [take["take_id"] for take in takes],
            "selected_take": selected_take,
            "round_status": round_status,
            "needs_prompt_revision": needs_prompt_revision,
            "storage_policy": "external_video_only",
        }
        self._write_yaml(review_path, review_payload)

        corrected_brief_path = None
        if needs_prompt_revision:
            corrected_brief_path = self._write_corrected_brief(
                prompt_id=prompt_id,
                takes=takes,
                review_notes=review_notes,
            )

        return VideoTakeReviewResult(
            video_takes_path=video_takes_path,
            review_path=review_path,
            corrected_brief_path=corrected_brief_path,
        )

    @staticmethod
    def _load_metadata(path: Path) -> Any:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)

    @staticmethod
    def _extract_takes(raw_metadata: Any) -> list[dict[str, Any]]:
        if isinstance(raw_metadata, list):
            return raw_metadata
        if isinstance(raw_metadata, dict) and isinstance(raw_metadata.get("takes"), list):
            return raw_metadata["takes"]
        raise VideoTakeReviewError("takes metadata must be a list or a mapping with takes")

    @staticmethod
    def _normalize_take(take: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(take, dict):
            raise VideoTakeReviewError("Each take must be a mapping.")

        take_id = str(take.get("take_id") or "").strip()
        status = str(take.get("status") or "").strip()
        reason = str(take.get("reason") or "").strip()
        if not take_id:
            raise VideoTakeReviewError("take_id is required")
        if status not in TAKE_STATUSES:
            raise VideoTakeReviewError(f"Unsupported take status: {status}")
        if not reason:
            raise VideoTakeReviewError("take reason is required")

        if bool(take.get("repo_binary_committed", False)):
            raise VideoTakeReviewError("repo_binary_committed must be false")

        quality_scores = take.get("quality_scores")
        if not isinstance(quality_scores, dict):
            raise VideoTakeReviewError("take quality_scores must be a dict")
        missing_scores = [field for field in QUALITY_SCORE_FIELDS if field not in quality_scores]
        if missing_scores:
            raise VideoTakeReviewError(f"Missing quality score fields: {missing_scores}")
        for field in QUALITY_SCORE_FIELDS:
            value = quality_scores[field]
            if not isinstance(value, int) or not 1 <= value <= 5:
                raise VideoTakeReviewError(f"{field} must be an integer from 1 to 5")

        failure_reason = take.get("failure_reason")
        if status in {"rejected", "needs_revision"} and failure_reason not in FAILURE_REASONS:
            raise VideoTakeReviewError(
                "Rejected or needs_revision takes require a valid failure_reason"
            )
        if failure_reason is not None and failure_reason not in FAILURE_REASONS:
            raise VideoTakeReviewError(f"Unsupported failure_reason: {failure_reason}")

        platform_asset_ref = take.get("platform_asset_ref")
        external_storage_ref = take.get("external_storage_ref")
        storage_status = take.get("storage_status")
        if not platform_asset_ref:
            storage_status = "pending_external"
        elif not storage_status:
            storage_status = "stored_external" if external_storage_ref else "pending_external"
        if storage_status not in STORAGE_STATUSES:
            raise VideoTakeReviewError(f"Unsupported storage_status: {storage_status}")

        external_missing_allowed = status == "candidate" and storage_status == "pending_external"
        if not external_storage_ref and not external_missing_allowed:
            raise VideoTakeReviewError(
                "external_storage_ref is required unless a candidate take is pending_external"
            )

        return {
            "take_id": take_id,
            "platform_asset_ref": str(platform_asset_ref).strip() if platform_asset_ref else None,
            "external_storage_ref": str(external_storage_ref).strip() if external_storage_ref else None,
            "local_proxy_ref": take.get("local_proxy_ref") or None,
            "repo_binary_committed": False,
            "storage_status": storage_status,
            "status": status,
            "reason": reason,
            "quality_scores": {field: quality_scores[field] for field in QUALITY_SCORE_FIELDS},
            "failure_reason": failure_reason,
        }

    @staticmethod
    def _selected_take_id(
        takes: list[dict[str, Any]],
        raw_metadata: Any,
    ) -> str | None:
        selected = [take["take_id"] for take in takes if take["status"] == "selected"]
        if len(selected) > 1:
            raise VideoTakeReviewError("At most one take may have status selected")
        selected_take = selected[0] if selected else None
        if isinstance(raw_metadata, dict) and raw_metadata.get("selected_take") is not None:
            explicit = str(raw_metadata["selected_take"])
            if explicit != selected_take:
                raise VideoTakeReviewError(
                    "selected_take must match the single take with status selected"
                )
        return selected_take

    @staticmethod
    def _needs_prompt_revision(
        *,
        takes: list[dict[str, Any]],
        raw_metadata: Any,
        selected_take: str | None,
    ) -> bool:
        if isinstance(raw_metadata, dict) and "needs_prompt_revision" in raw_metadata:
            return bool(raw_metadata["needs_prompt_revision"])
        if selected_take is None:
            return True
        return any(take["status"] == "needs_revision" for take in takes)

    def _write_corrected_brief(
        self,
        *,
        prompt_id: str,
        takes: list[dict[str, Any]],
        review_notes: str,
    ) -> Path:
        out_path = (
            self.repo_root
            / "evidence"
            / "prompt_reviews"
            / f"{self._next_prompt_brief_id(prompt_id)}_brief.yaml"
        )
        payload = {
            "source_prompt_id": prompt_id,
            "corrected_brief": {
                "revision_reason": "Video take review requires prompt revision.",
                "review_notes": review_notes,
                "failed_take_ids": [
                    take["take_id"]
                    for take in takes
                    if take["status"] in {"rejected", "needs_revision"}
                ],
                "failure_reasons": sorted(
                    {
                        take["failure_reason"]
                        for take in takes
                        if take.get("failure_reason") is not None
                    }
                ),
            },
        }
        self._write_yaml(out_path, payload)
        return out_path

    @staticmethod
    def _next_prompt_brief_id(source_prompt_id: str) -> str:
        match = PROMPT_VERSION_RE.match(source_prompt_id)
        if not match:
            raise VideoTakeReviewError(f"Invalid prompt_id: {source_prompt_id}")
        next_version = int(match.group("version")) + 1
        return f"{match.group('stem')}__v{next_version:02d}"

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.repo_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
