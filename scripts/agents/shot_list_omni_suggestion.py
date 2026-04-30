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

    def build(self, scene_id: str, *, write: bool = True) -> ShotListOmniSuggestionResult:
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

        source_refs = storyboard.get("source_refs")
        if not isinstance(source_refs, dict):
            source_refs = {}

        payload = {
            "scene_id": scene_id,
            "source_storyboard_option": selected_option_id,
            "source_refs": {
                "storyboard_options": storyboard_path.relative_to(self.repo_root).as_posix(),
                "scene_card": _source_text(
                    source_refs.get("scene_card"),
                    f"planning/scenes/{scene_id}/scene_card.yaml",
                ),
                "scene_excerpt": _source_text(
                    source_refs.get("scene_excerpt"),
                    f"planning/scenes/{scene_id}/scene_excerpt.md",
                ),
            },
            "suggested_shot_list": [
                self._build_shot(scene_id, selected_index, selected_option)
            ],
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
    def _build_shot(
        scene_id: str,
        selected_index: int,
        option: dict[str, Any],
    ) -> dict[str, Any]:
        option_field = f"options[{selected_index}]"
        lighting = _source_text(option.get("lighting"), "No source-stated lighting.")
        status = _source_text(option.get("status"), "candidate")
        return {
            "shot_id": f"{scene_id}_OMNI01",
            "type": "single_omni_shot",
            "subject": _source_text(option.get("purpose"), "Selected storyboard option."),
            "camera_angle": _source_text(
                option.get("camera_angle"),
                "EVIDENCE_THIN: no source-stated camera angle.",
            ),
            "framing": _source_text(
                option.get("framing"),
                "EVIDENCE_THIN: no source-stated framing.",
            ),
            "camera_movement": _source_text(
                option.get("movement"),
                "EVIDENCE_THIN: no source-stated movement.",
            ),
            "duration_seconds": 5,
            "source_field": _source_text(
                option.get("source_field"),
                "storyboard_options.selected_option",
            ),
            "source_option_field": option_field,
            "notes": f"Lighting: {lighting}. Storyboard option status: {status}.",
        }
