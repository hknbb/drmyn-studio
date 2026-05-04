"""
Storyboard Options Agent for Batch 5.75.

Generates metadata-only storyboard option boards. It reads source scene records
and writes candidate composition metadata, but never selects an option and never
creates image or video binaries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


UNRESOLVED_RE = re.compile(r"\b(UNRESOLVED|TODO_REVIEW|TODO|EVIDENCE_THIN)\b")

VISUAL_TARGET_FIELDS = (
    ("palette", "Represent the source-stated palette and material atmosphere."),
    ("lens_bias", "Represent the source-stated lens and coverage behavior."),
    ("framing_bias", "Represent the source-stated framing geometry."),
    ("movement_bias", "Represent the source-stated movement logic."),
    ("lighting_bias", "Represent the source-stated lighting treatment."),
)

DURATION_PROFILES = (
    {
        "total_duration_seconds": 5,
        "recommended_shot_count": 1,
        "rhythm": "single held coverage beat",
    },
    {
        "total_duration_seconds": 10,
        "recommended_shot_count": 2,
        "rhythm": "establish the scene geometry, then register the source-stated action beat",
    },
    {
        "total_duration_seconds": 15,
        "recommended_shot_count": 3,
        "rhythm": "establish the geometry, isolate the source-stated deviation, then hold reaction",
    },
)

COVERAGE_STRATEGIES = {
    "palette": "environmental_atmosphere_coverage",
    "lens_bias": "intimate_behavioral_coverage",
    "framing_bias": "threshold_geometry_coverage",
    "movement_bias": "route_logic_coverage",
    "lighting_bias": "lighting_continuity_coverage",
}


class StoryboardOptionsError(ValueError):
    """Raised when storyboard options cannot be grounded in scene sources."""


@dataclass(frozen=True)
class StoryboardOptionsResult:
    """Path and payload written for one storyboard option board."""

    storyboard_options_path: Path
    payload: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _source_value(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _status_for_option(field_name: str, visual_targets: dict[str, Any]) -> str:
    values = [
        visual_targets.get(field_name),
        visual_targets.get("lens_bias"),
        visual_targets.get("framing_bias"),
        visual_targets.get("movement_bias"),
        visual_targets.get("lighting_bias"),
    ]
    for value in values:
        if isinstance(value, str) and UNRESOLVED_RE.search(value):
            return "blocked"
    for value in values:
        if not isinstance(value, str) or not value.strip():
            return "evidence_thin"
    return "candidate"


class StoryboardOptionsAgent:
    """Build scene-grounded storyboard option boards."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def build(
        self,
        scene_id: str,
        *,
        round_number: int = 1,
        write: bool = True,
    ) -> StoryboardOptionsResult:
        """Build at least five candidate options for a scene."""
        scene_dir = self.repo_root / "planning" / "scenes" / scene_id
        scene_card_path = scene_dir / "scene_card.yaml"
        scene_card = _read_yaml(scene_card_path)
        if scene_card is None:
            raise StoryboardOptionsError(f"Missing scene card: {scene_card_path}")

        excerpt_ref = str(scene_card.get("excerpt_ref") or "scene_excerpt.md")
        scene_excerpt_path = scene_dir / excerpt_ref
        scene_excerpt = _read_text(scene_excerpt_path)
        if scene_excerpt is None:
            raise StoryboardOptionsError(f"Missing scene excerpt: {scene_excerpt_path}")

        visual_targets = scene_card.get("visual_targets") or {}
        if not isinstance(visual_targets, dict):
            visual_targets = {}

        aesthetic_pack_refs: list[str] = list(
            visual_targets.get("aesthetic_pack_refs") or []
        )

        payload = {
            "scene_id": scene_id,
            "round": round_number,
            "source_refs": {
                "scene_card": scene_card_path.relative_to(self.repo_root).as_posix(),
                "scene_excerpt": scene_excerpt_path.relative_to(self.repo_root).as_posix(),
            },
            "options": self._build_options(scene_id, visual_targets, aesthetic_pack_refs),
            "selected_option": None,
            "review_status": "pending",
            "storage_policy": "no_binary_commits",
        }

        out_path = (
            self.repo_root
            / "visual_dev"
            / "storyboards"
            / scene_id
            / "storyboard_options.yaml"
        )
        if write:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

        return StoryboardOptionsResult(
            storyboard_options_path=out_path,
            payload=payload,
        )

    @staticmethod
    def _build_options(
        scene_id: str,
        visual_targets: dict[str, Any],
        aesthetic_pack_refs: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        lens_bias = _source_value(
            visual_targets.get("lens_bias"),
            "EVIDENCE_THIN: no source-stated lens or camera-angle bias.",
        )
        framing_bias = _source_value(
            visual_targets.get("framing_bias"),
            "EVIDENCE_THIN: no source-stated framing bias.",
        )
        movement_bias = _source_value(
            visual_targets.get("movement_bias"),
            "EVIDENCE_THIN: no source-stated movement bias.",
        )
        lighting_bias = _source_value(
            visual_targets.get("lighting_bias"),
            "EVIDENCE_THIN: no source-stated lighting bias.",
        )

        pack_refs = list(aesthetic_pack_refs) if aesthetic_pack_refs else []
        options: list[dict[str, Any]] = []
        for index, (field_name, purpose_prefix) in enumerate(VISUAL_TARGET_FIELDS, start=1):
            field_value = visual_targets.get(field_name)
            status = _status_for_option(field_name, visual_targets)
            source_text = _source_value(
                field_value,
                f"EVIDENCE_THIN: scene_card.visual_targets.{field_name} is missing.",
            )
            option: dict[str, Any] = {
                "option_id": f"{scene_id}_SB{index:02d}",
                "purpose": f"{purpose_prefix} Source: {source_text}",
                "coverage_strategy": COVERAGE_STRATEGIES[field_name],
                "scene_action_type": "static_tension",
                "duration_profiles": [dict(profile) for profile in DURATION_PROFILES],
                "coverage_shots": StoryboardOptionsAgent._build_coverage_shots(
                    field_name=field_name,
                    source_text=source_text,
                    lens_bias=lens_bias,
                    framing_bias=framing_bias,
                    movement_bias=movement_bias,
                    lighting_bias=lighting_bias,
                ),
                "camera_angle": lens_bias,
                "framing": framing_bias,
                "movement": movement_bias,
                "lighting": lighting_bias,
                "source_field": f"scene_card.visual_targets.{field_name}",
                "prompt_ids": [],
                "status": status,
            }
            if pack_refs:
                option["aesthetic_pack_refs"] = pack_refs
            options.append(option)

        return options

    @staticmethod
    def _build_coverage_shots(
        *,
        field_name: str,
        source_text: str,
        lens_bias: str,
        framing_bias: str,
        movement_bias: str,
        lighting_bias: str,
    ) -> list[dict[str, Any]]:
        source_field = f"scene_card.visual_targets.{field_name}"
        return [
            {
                "role": "establish_coverage",
                "subject": f"Establish the scene treatment through: {source_text}",
                "camera_angle": lens_bias,
                "framing": framing_bias,
                "camera_movement": movement_bias,
                "lighting": lighting_bias,
                "min_duration_seconds": 2,
                "max_duration_seconds": 5,
                "source_field": source_field,
            },
            {
                "role": "action_or_deviation_coverage",
                "subject": "Register the source-stated action beat without adding new story facts.",
                "camera_angle": lens_bias,
                "framing": framing_bias,
                "camera_movement": movement_bias,
                "lighting": lighting_bias,
                "min_duration_seconds": 2,
                "max_duration_seconds": 5,
                "source_field": source_field,
            },
            {
                "role": "reaction_or_hold_coverage",
                "subject": "Hold the scene response within the selected visual treatment.",
                "camera_angle": lens_bias,
                "framing": framing_bias,
                "camera_movement": movement_bias,
                "lighting": lighting_bias,
                "min_duration_seconds": 2,
                "max_duration_seconds": 5,
                "source_field": source_field,
            },
        ]
