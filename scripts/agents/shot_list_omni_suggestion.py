"""
Shot List Omni Suggestion Agent for Batch 7.5.

Reads a human-selected storyboard option and writes a metadata-only
shot_list_omni_suggestion.yaml. It never modifies scene_card.yaml,
storyboard_options.yaml, selected_option, lifecycle fields, or binaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.agents.omni_duration_planner import plan_omni_duration


class ShotListOmniSuggestionError(ValueError):
    """Raised when a shot list suggestion cannot be safely produced."""


@dataclass(frozen=True)
class ShotListOmniSuggestionResult:
    suggestion_path: Path
    payload: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _source_text(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


class ShotListOmniSuggestionAgent:
    """Create metadata-only shot_list_omni suggestions from selected storyboard options."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def build(
        self,
        scene_id: str,
        *,
        target_duration_seconds: int = 10,
        write: bool = True,
    ) -> ShotListOmniSuggestionResult:
        storyboard_path = (
            self.repo_root
            / "visual_dev"
            / "storyboards"
            / scene_id
            / "storyboard_options.yaml"
        )
        storyboard = _read_yaml(storyboard_path)
        if storyboard is None:
            raise ShotListOmniSuggestionError(
                f"Missing storyboard options: {storyboard_path}"
            )

        selected_option_id = storyboard.get("selected_option")
        if not isinstance(selected_option_id, str) or not selected_option_id.strip():
            raise ShotListOmniSuggestionError(
                f"{scene_id} is not ready: selected_option is not set."
            )

        options = storyboard.get("options")
        if not isinstance(options, list):
            raise ShotListOmniSuggestionError("storyboard options must be a list.")

        selected_index = None
        selected_option = None
        for index, option in enumerate(options):
            if isinstance(option, dict) and option.get("option_id") == selected_option_id:
                selected_index = index
                selected_option = option
                break
        if selected_option is None or selected_index is None:
            raise ShotListOmniSuggestionError(
                f"selected_option {selected_option_id!r} does not match any option_id."
            )

        scene_action_type = _source_text(
            selected_option.get("scene_action_type"),
            "static_tension",
        )
        try:
            duration_plan = plan_omni_duration(scene_action_type, target_duration_seconds)
        except ValueError as exc:
            raise ShotListOmniSuggestionError(str(exc)) from exc

        coverage_strategy = _source_text(
            selected_option.get("coverage_strategy"),
            "source_grounded_single_option_coverage",
        )

        payload = {
            "scene_id": scene_id,
            "source_storyboard_options": storyboard_path.relative_to(
                self.repo_root
            ).as_posix(),
            "source_selected_option": selected_option_id,
            "target_duration_seconds": target_duration_seconds,
            "coverage_strategy": coverage_strategy,
            "scene_action_type": scene_action_type,
            "duration_plan": duration_plan,
            "suggested_shot_list": self._build_shots(
                scene_id=scene_id,
                selected_option_id=selected_option_id,
                option=selected_option,
                duration_slots=list(duration_plan["duration_slots"]),
            ),
            "suggested_by": "storyboard_agent",
            "applied_to_scene_card": False,
            "applied_at": None,
            "review_status": "pending",
            "storage_policy": "no_binary_commits",
        }

        out_path = (
            self.repo_root
            / "visual_dev"
            / "storyboards"
            / scene_id
            / "shot_list_omni_suggestion.yaml"
        )
        if write:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

        return ShotListOmniSuggestionResult(suggestion_path=out_path, payload=payload)

    @staticmethod
    def _build_shots(
        *,
        scene_id: str,
        selected_option_id: str,
        option: dict[str, Any],
        duration_slots: list[int],
    ) -> list[dict[str, Any]]:
        coverage_shots = option.get("coverage_shots")
        if not isinstance(coverage_shots, list) or not coverage_shots:
            coverage_shots = [
                {
                    "role": "selected_option_coverage",
                    "subject": _source_text(
                        option.get("purpose"),
                        "Selected storyboard option.",
                    ),
                    "camera_angle": option.get("camera_angle"),
                    "framing": option.get("framing"),
                    "camera_movement": option.get("movement"),
                    "lighting": option.get("lighting"),
                }
            ]

        shots: list[dict[str, Any]] = []
        for index, duration_seconds in enumerate(duration_slots, start=1):
            coverage_shot = coverage_shots[min(index - 1, len(coverage_shots) - 1)]
            if not isinstance(coverage_shot, dict):
                coverage_shot = {}
            shots.append(
                {
                    "shot_id": f"{scene_id}_OMNI{index:02d}",
                    "role": _source_text(coverage_shot.get("role"), "coverage"),
                    "subject": _source_text(
                        coverage_shot.get("subject"),
                        _source_text(option.get("purpose"), "Selected storyboard option."),
                    ),
                    "camera_angle": _source_text(
                        coverage_shot.get("camera_angle") or option.get("camera_angle"),
                        "EVIDENCE_THIN: no source-stated camera angle.",
                    ),
                    "framing": _source_text(
                        coverage_shot.get("framing") or option.get("framing"),
                        "EVIDENCE_THIN: no source-stated framing.",
                    ),
                    "camera_movement": _source_text(
                        coverage_shot.get("camera_movement") or option.get("movement"),
                        "EVIDENCE_THIN: no source-stated movement.",
                    ),
                    "lighting": _source_text(
                        coverage_shot.get("lighting") or option.get("lighting"),
                        "EVIDENCE_THIN: no source-stated lighting.",
                    ),
                    "duration_seconds": duration_seconds,
                    "source_storyboard_option": selected_option_id,
                    "source_coverage_role": _source_text(
                        coverage_shot.get("role"),
                        "selected_option_coverage",
                    ),
                }
            )
        return shots
