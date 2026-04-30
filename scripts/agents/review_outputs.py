"""
Image Review Agent for Batch 5.5.

This agent writes metadata only. It records selection decisions, clearance
records, and pack-manifest suggestions, but it never copies image binaries and
never updates pack lifecycle state directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


QUALITY_SCORE_FIELDS = (
    "identity_consistency",
    "source_grounding",
    "style_compliance",
    "continuity",
    "production_usability",
)

FAILURE_REASONS = (
    "source_missing",
    "continuity_unresolved",
    "model_guidance_stale",
    "output_too_stylized",
    "identity_drift",
    "camera_drift",
    "storage_policy_violation",
    "schema_validation_error",
    "unsourced_assertion",
    "continuity_contradiction",
)

ELEMENT_TYPE_TO_DIR = {
    "character": "characters",
    "characters": "characters",
    "location": "locations",
    "locations": "locations",
    "prop": "props",
    "props": "props",
    "wardrobe": "wardrobe",
    "style_ref": "style_refs",
    "style_refs": "style_refs",
}

DIR_TO_ELEMENT_TYPE = {
    "characters": "character",
    "locations": "location",
    "props": "prop",
    "wardrobe": "wardrobe",
    "style_refs": "style_ref",
}

PROMPT_VERSION_RE = re.compile(r"^(?P<stem>SC\d{4}__[a-z0-9\-]+)__v(?P<version>\d{2})$")


class ReviewOutputError(ValueError):
    """Raised when review metadata would violate Batch 5.5 rules."""


@dataclass(frozen=True)
class ReviewWriteResult:
    """Paths written by one image review operation."""

    image_selection_path: Path
    pack_manifest_suggestion_path: Path
    asset_clearance_paths: tuple[Path, ...]
    corrected_brief_path: Path | None


class ImageReviewAgent:
    """Write metadata-only image review records."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def write_review(
        self,
        *,
        element_type: str,
        element_id: str,
        source_prompt_ids: list[str],
        source_model: str,
        candidate_images: list[dict[str, Any]],
        canonical_images: list[str] | None = None,
        selection_round: int = 1,
        review_notes: str = "",
        corrected_brief: dict[str, Any] | None = None,
    ) -> ReviewWriteResult:
        """
        Write image review metadata for one element pack.

        ``candidate_images`` are metadata dictionaries, not binary files. Each
        candidate must include path, status, reason, and the five quality score
        fields. Rejected candidates must include a failure_reason.
        """

        element_dir_name = self._element_dir_name(element_type)
        normalized_element_type = DIR_TO_ELEMENT_TYPE[element_dir_name]
        element_dir = (
            self.repo_root
            / "visual_dev"
            / "elements"
            / element_dir_name
            / element_id
        )

        canonical_images = list(canonical_images or [])
        normalized_candidates = [
            self._normalize_candidate(candidate)
            for candidate in candidate_images
        ]
        if not normalized_candidates:
            raise ReviewOutputError("candidate_images must not be empty")

        round_status = "complete" if canonical_images else "needs_prompt_revision"
        selection_record = {
            "element_id": element_id,
            "element_type": normalized_element_type,
            "selection_round": selection_round,
            "source_prompt_ids": source_prompt_ids,
            "candidate_images": normalized_candidates,
            "canonical_images": canonical_images,
            "round_status": round_status,
            "pack_manifest_sync": "pending",
            "review_notes": review_notes,
        }

        image_selection_path = element_dir / "image_selection.yaml"
        self._write_yaml(image_selection_path, selection_record)

        suggestion_path = element_dir / "pack_manifest_update_suggestion.yaml"
        self._write_yaml(
            suggestion_path,
            self._build_pack_manifest_suggestion(
                element_id=element_id,
                canonical_images=canonical_images,
            ),
        )

        clearance_paths = tuple(
            self._write_clearance_records(
                element_id=element_id,
                element_type=normalized_element_type,
                source_prompt_id=source_prompt_ids[0],
                source_model=source_model,
                candidates=normalized_candidates,
                canonical_images=canonical_images,
                review_notes=review_notes,
            )
        )

        corrected_brief_path = None
        if corrected_brief is not None:
            corrected_brief_path = self._write_corrected_brief(
                source_prompt_ids[0],
                corrected_brief,
            )

        return ReviewWriteResult(
            image_selection_path=image_selection_path,
            pack_manifest_suggestion_path=suggestion_path,
            asset_clearance_paths=clearance_paths,
            corrected_brief_path=corrected_brief_path,
        )

    @staticmethod
    def _element_dir_name(element_type: str) -> str:
        try:
            return ELEMENT_TYPE_TO_DIR[element_type]
        except KeyError as exc:
            raise ReviewOutputError(f"Unsupported element_type: {element_type}") from exc

    @staticmethod
    def _normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
        status = candidate.get("status")
        if status not in {"candidate", "selected", "rejected", "canonical", "deprecated"}:
            raise ReviewOutputError(f"Unsupported candidate status: {status}")

        quality_scores = candidate.get("quality_scores")
        if not isinstance(quality_scores, dict):
            raise ReviewOutputError("candidate quality_scores must be a dict")
        missing_scores = [
            field for field in QUALITY_SCORE_FIELDS if field not in quality_scores
        ]
        if missing_scores:
            raise ReviewOutputError(f"Missing quality score fields: {missing_scores}")
        for field in QUALITY_SCORE_FIELDS:
            value = quality_scores[field]
            if not isinstance(value, int) or not 1 <= value <= 5:
                raise ReviewOutputError(f"{field} must be an integer from 1 to 5")

        failure_reason = candidate.get("failure_reason")
        if status == "rejected" and failure_reason not in FAILURE_REASONS:
            raise ReviewOutputError(
                "Rejected candidates require a valid failure_reason"
            )
        if failure_reason is not None and failure_reason not in FAILURE_REASONS:
            raise ReviewOutputError(f"Unsupported failure_reason: {failure_reason}")

        path = str(candidate.get("path") or "").strip()
        if not path:
            raise ReviewOutputError("candidate path is required")

        normalized = {
            "path": path,
            "status": status,
            "reason": str(candidate.get("reason") or "").strip(),
            "quality_scores": {field: quality_scores[field] for field in QUALITY_SCORE_FIELDS},
            "failure_reason": failure_reason,
            "repo_binary_committed": bool(candidate.get("repo_binary_committed", False)),
        }
        if not normalized["reason"]:
            raise ReviewOutputError("candidate reason is required")
        if candidate.get("asset_id"):
            normalized["asset_id"] = str(candidate["asset_id"])
        if "external_storage_ref" in candidate:
            normalized["external_storage_ref"] = candidate["external_storage_ref"]
        return normalized

    @staticmethod
    def _build_pack_manifest_suggestion(
        *,
        element_id: str,
        canonical_images: list[str],
    ) -> dict[str, Any]:
        seeded = bool(canonical_images)
        return {
            "element_id": element_id,
            "suggested_field": "pack_status",
            "suggested_value": "seeded" if seeded else "metadata_only",
            "reason": (
                "image_selection.yaml complete with canonical_images non-empty"
                if seeded
                else "No canonical_images selected; keep pack metadata-only"
            ),
            "applied_by": None,
            "applied_at": None,
        }

    def _write_clearance_records(
        self,
        *,
        element_id: str,
        element_type: str,
        source_prompt_id: str,
        source_model: str,
        candidates: list[dict[str, Any]],
        canonical_images: list[str],
        review_notes: str,
    ) -> list[Path]:
        selected_paths = set(canonical_images)
        selected_paths.update(
            candidate["path"]
            for candidate in candidates
            if candidate["status"] in {"selected", "canonical"}
        )

        paths: list[Path] = []
        for asset_path in sorted(selected_paths):
            candidate = next(
                (item for item in candidates if item["path"] == asset_path),
                {},
            )
            asset_id = str(candidate.get("asset_id") or self._asset_id(element_id, asset_path))
            clearance = {
                "asset_id": asset_id,
                "element_id": element_id,
                "element_type": element_type,
                "asset_path": asset_path,
                "source_prompt_id": source_prompt_id,
                "source_model": source_model,
                "commercial_use_allowed": "pending_review",
                "actor_likeness_risk": False,
                "style_imitation_risk": False,
                "watermark_detected": False,
                "face_identity_drift": False,
                "review_notes": review_notes,
                "clearance_status": "pending_review",
            }
            out_path = self.repo_root / "evidence" / "asset_clearance" / f"{asset_id}.yaml"
            self._write_yaml(out_path, clearance)
            paths.append(out_path)
        return paths

    def _write_corrected_brief(
        self,
        source_prompt_id: str,
        corrected_brief: dict[str, Any],
    ) -> Path:
        out_path = (
            self.repo_root
            / "evidence"
            / "prompt_reviews"
            / f"{self._next_prompt_brief_id(source_prompt_id)}_brief.yaml"
        )
        payload = {
            "source_prompt_id": source_prompt_id,
            "corrected_brief": corrected_brief,
        }
        self._write_yaml(out_path, payload)
        return out_path

    @staticmethod
    def _asset_id(element_id: str, asset_path: str) -> str:
        stem = Path(asset_path).stem
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("_")
        return f"{element_id}_{safe_stem}"

    @staticmethod
    def _next_prompt_brief_id(source_prompt_id: str) -> str:
        match = PROMPT_VERSION_RE.match(source_prompt_id)
        if not match:
            raise ReviewOutputError(f"Invalid prompt_id: {source_prompt_id}")
        next_version = int(match.group("version")) + 1
        return f"{match.group('stem')}__v{next_version:02d}"

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
