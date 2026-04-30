"""
Kling Omni metadata-only prompt adapter for Batch 8.

This adapter writes draft prompt/run metadata for external Kling generation.
It never calls Kling, never writes video binaries, and never creates video take
review or selected clip records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


CANONICAL_ID_RE = re.compile(r"\b(SC\d{4}|C\d{2}|LOC\d{3}|PROP\d{3}|WD\d{3})\b")


class KlingOmniAdapterError(ValueError):
    """Raised when Phase 3 Kling prompt gates are not satisfied."""


@dataclass(frozen=True)
class KlingOmniBuildResult:
    prompt_record: dict[str, Any]
    run_record: dict[str, Any]
    warnings: list[str]


def _read_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _sanitize_prompt_text(text: str) -> str:
    text = CANONICAL_ID_RE.sub("the referenced production element", text)
    return " ".join(text.split())


class KlingOmniAdapter:
    """Build draft Kling Omni prompt records from human-approved scene metadata."""

    MODEL_ID = "kling_omni"
    MODEL_SLUG = "kling-omni"
    ABBREV = "KO"

    def __init__(
        self,
        repo_root: str | Path,
        *,
        model_guidance_mode: str = "locked_guide",
        model_guidance_snapshot: str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.model_guidance_mode = model_guidance_mode
        self.model_guidance_snapshot = model_guidance_snapshot

    def generate(
        self,
        scene_id: str,
        *,
        version: int = 1,
        run_counter: int = 1,
        run_at: str | None = None,
    ) -> KlingOmniBuildResult:
        scene_card_path = self.repo_root / "planning" / "scenes" / scene_id / "scene_card.yaml"
        scene_card = _read_yaml(scene_card_path)
        if scene_card is None:
            raise KlingOmniAdapterError(f"Missing scene card: {scene_card_path}")

        shot_list = scene_card.get("shot_list_omni")
        if not isinstance(shot_list, list) or not shot_list:
            raise KlingOmniAdapterError(
                f"{scene_id} blocked: scene_card.shot_list_omni is empty."
            )

        omni_set_ref = _text(scene_card.get("omni_set_ref"))
        if not omni_set_ref:
            raise KlingOmniAdapterError(
                f"{scene_id} blocked: scene_card.omni_set_ref is missing."
            )

        warnings = self._pack_gate_warnings(scene_id, omni_set_ref)
        blocking = [warning for warning in warnings if warning.startswith("BLOCKED:")]
        if blocking:
            raise KlingOmniAdapterError("; ".join(blocking))

        storyboard_options_path = (
            self.repo_root / "visual_dev" / "storyboards" / scene_id / "storyboard_options.yaml"
        )
        storyboard_options = _read_yaml(storyboard_options_path)
        if storyboard_options is not None and not storyboard_options.get("selected_option"):
            raise KlingOmniAdapterError(
                f"{scene_id} blocked: storyboard_options.yaml has no selected_option."
            )

        suggestion_path = (
            self.repo_root
            / "visual_dev"
            / "storyboards"
            / scene_id
            / "shot_list_omni_suggestion.yaml"
        )

        prompt_record = self._prompt_record(
            scene_id=scene_id,
            scene_card=scene_card,
            shot_list=shot_list,
            scene_card_path=scene_card_path,
            storyboard_options_path=storyboard_options_path,
            suggestion_path=suggestion_path,
            omni_set_ref=omni_set_ref,
            version=version,
        )
        run_record = self._run_record(
            scene_id=scene_id,
            prompt_id=prompt_record["prompt_id"],
            run_counter=run_counter,
            run_at=run_at,
        )
        return KlingOmniBuildResult(
            prompt_record=prompt_record,
            run_record=run_record,
            warnings=warnings,
        )

    def _prompt_record(
        self,
        *,
        scene_id: str,
        scene_card: dict[str, Any],
        shot_list: list[Any],
        scene_card_path: Path,
        storyboard_options_path: Path,
        suggestion_path: Path,
        omni_set_ref: str,
        version: int,
    ) -> dict[str, Any]:
        prompt_id = f"{scene_id}__omni-kling-omni__v{version:02d}"
        max_duration = self._max_duration_seconds()
        prompt_text = self._build_prompt_text(scene_card, shot_list, max_duration)
        source_refs: dict[str, Any] = {
            "scene_card": _relative(scene_card_path, self.repo_root),
            "scene_excerpt": f"planning/scenes/{scene_id}/{scene_card.get('excerpt_ref') or 'scene_excerpt.md'}",
            "omni_set_ref": omni_set_ref,
        }
        if storyboard_options_path.exists():
            source_refs["storyboard_options"] = _relative(
                storyboard_options_path, self.repo_root
            )
        if suggestion_path.exists():
            source_refs["shot_list_omni_suggestion"] = _relative(
                suggestion_path, self.repo_root
            )

        generation_params: dict[str, Any] = {
            "model_guidance_mode": self.model_guidance_mode,
            "model_guidance_ref": "docs/model_guides/kling_omni.yaml",
            "adapter_name": self.MODEL_ID,
            "constraint_strategy": "embedded_positive_constraints",
            "max_duration_seconds": max_duration,
            "repo_binary_committed": False,
            "external_generation_required": True,
        }
        if self.model_guidance_snapshot:
            generation_params["model_guidance_snapshot"] = self.model_guidance_snapshot

        return {
            "prompt_id": prompt_id,
            "scene_id": scene_id,
            "prompt_type": "omni_instruction",
            "lifecycle_stage": "draft",
            "target_models": [self.MODEL_ID],
            "source_refs": source_refs,
            "prompt_text": prompt_text,
            "generation_params": generation_params,
            "expected_output": {
                "asset_type": "clip",
                "duration_seconds": min(
                    self._shot_duration_total(shot_list),
                    max_duration,
                ),
            },
            "status": "active",
            "canon_lock": False,
        }

    def _run_record(
        self,
        *,
        scene_id: str,
        prompt_id: str,
        run_counter: int,
        run_at: str | None,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "run_id": f"RUN_{scene_id}_{self.ABBREV}_{run_counter:04d}",
            "prompt_id": prompt_id,
            "model": self.MODEL_ID,
            "run_at": run_at or _now_iso(),
            "outputs_expected": 1,
            "cost": {"unit": "unknown", "value": 0},
            "status": "pending",
        }
        if self.model_guidance_snapshot:
            record["model_guidance_snapshot"] = self.model_guidance_snapshot
        return record

    def _build_prompt_text(
        self,
        scene_card: dict[str, Any],
        shot_list: list[Any],
        max_duration: int,
    ) -> str:
        scene_title = _text(scene_card.get("title"), "Selected scene")
        purpose = _text(scene_card.get("purpose"), "")
        visual_targets = scene_card.get("visual_targets")
        if not isinstance(visual_targets, dict):
            visual_targets = {}
        shots: list[str] = []
        for index, shot in enumerate(shot_list[:3], start=1):
            if not isinstance(shot, dict):
                shots.append(f"Shot {index}: follow the approved Omni shot guidance.")
                continue
            subject = _text(shot.get("subject"), "approved scene subject")
            framing = _text(shot.get("framing"), "source-grounded framing")
            movement = _text(
                shot.get("camera_movement") or shot.get("movement"),
                "controlled camera movement",
            )
            duration = shot.get("duration_seconds")
            duration_text = f"{duration}s" if isinstance(duration, (int, float)) else "brief"
            shots.append(
                f"Shot {index}: {subject}; {framing}; {movement}; {duration_text}."
            )
        parts = [
            "Create one external Kling Omni video instruction.",
            f"Scene tone: {scene_title}.",
        ]
        if purpose:
            parts.append(f"Dramatic intent: {purpose}.")
        parts.extend(shots)
        if visual_targets:
            parts.append(
                "Visual treatment: "
                + "; ".join(
                    _text(visual_targets.get(key))
                    for key in ("palette", "framing_bias", "movement_bias", "lighting_bias")
                    if _text(visual_targets.get(key))
                )
                + "."
            )
        parts.append(
            f"Keep the clip under {max_duration} seconds. Do not add new story facts."
        )
        return _sanitize_prompt_text(" ".join(part for part in parts if part))

    def _pack_gate_warnings(self, scene_id: str, omni_set_ref: str) -> list[str]:
        warnings: list[str] = []
        element_set_path = self.repo_root / omni_set_ref / "element_set.yaml"
        element_set = _read_yaml(element_set_path)
        if element_set is None:
            warnings.append(
                f"WARNING: no element_set.yaml found for {scene_id}; pack lock status could not be verified."
            )
            return warnings

        refs = element_set.get("element_refs") or []
        if not isinstance(refs, list):
            warnings.append("WARNING: element_set.element_refs is not a list.")
            return warnings

        for ref in refs:
            ref_path = self.repo_root / str(ref)
            element_ref = _read_yaml(ref_path)
            if not isinstance(element_ref, dict):
                warnings.append(f"WARNING: missing element descriptor: {ref}")
                continue
            pack_path = _text(element_ref.get("pack_path_expected"))
            if not pack_path:
                warnings.append(f"WARNING: no pack_path_expected in {ref}")
                continue
            pack_manifest_path = self.repo_root / pack_path / "pack_manifest.yaml"
            pack_manifest = _read_yaml(pack_manifest_path)
            if pack_manifest is None:
                warnings.append(f"WARNING: no pack_manifest.yaml at {pack_path}")
                continue
            status = pack_manifest.get("pack_status")
            if status != "locked":
                warnings.append(
                    f"BLOCKED: {pack_path} pack_status is {status!r}, expected 'locked'."
                )
        return warnings

    def _max_duration_seconds(self) -> int:
        matrix_path = self.repo_root / "docs" / "model_guides" / "model_capability_matrix.yaml"
        matrix = _read_yaml(matrix_path) or {}
        models = matrix.get("models") if isinstance(matrix, dict) else {}
        kling = models.get("kling_omni") if isinstance(models, dict) else {}
        value = kling.get("max_duration_seconds") if isinstance(kling, dict) else None
        return int(value) if isinstance(value, int) else 10

    @staticmethod
    def _shot_duration_total(shot_list: list[Any]) -> int:
        total = 0
        for shot in shot_list:
            if isinstance(shot, dict) and isinstance(shot.get("duration_seconds"), int):
                total += int(shot["duration_seconds"])
        return total or 5
