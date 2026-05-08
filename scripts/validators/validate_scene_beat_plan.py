"""
Semantic validator for scene_beat_plan records.

Enforces cross-beat rules that JSON Schema cannot express:
1. beat_id uniqueness within a single scene
2. Defensive duration_seconds rejection (schema already blocks, validator confirms)
3. Batch validation across multiple scene records
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SceneBeatPlanValidationError(Exception):
    """Raised on semantic validation failure."""

    scene_id: str
    error_code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.scene_id}] {self.error_code}: {self.message}"


def validate_scene_beat_plan(record: dict[str, Any]) -> list[SceneBeatPlanValidationError]:
    """
    Validate a single scene_beat_plan record for semantic correctness.

    Rules enforced:
    1. beat_id values must be unique within source_beats array
    2. duration_seconds must not appear at scene level or beat level

    Args:
        record: scene_beat_plan record (already validated by JSON Schema)

    Returns:
        List of validation errors (empty if record is valid)

    Raises:
        No exceptions; returns error list for caller to handle
    """
    errors: list[SceneBeatPlanValidationError] = []
    scene_id = record.get("scene_id", "UNKNOWN")

    # Rule 1: beat_id uniqueness
    source_beats = record.get("source_beats", [])
    beat_ids = [beat.get("beat_id") for beat in source_beats]
    seen_ids: set[str] = set()
    for beat_id in beat_ids:
        if beat_id in seen_ids:
            errors.append(
                SceneBeatPlanValidationError(
                    scene_id=scene_id,
                    error_code="DUPLICATE_BEAT_ID",
                    message=f"[{scene_id}] beat_id {beat_id!r} appears multiple times in source_beats; must be unique within scene",
                )
            )
        else:
            seen_ids.add(beat_id)

    # Rule 2: duration_seconds defensive check (schema already rejects, but validate defensively)
    if "duration_seconds" in record:
        errors.append(
            SceneBeatPlanValidationError(
                scene_id=scene_id,
                error_code="DURATION_SECONDS_AT_SCENE",
                message="duration_seconds must not appear at scene level; durations are computed by packer in A5/B6",
            )
        )

    for idx, beat in enumerate(source_beats):
        if "duration_seconds" in beat:
            errors.append(
                SceneBeatPlanValidationError(
                    scene_id=scene_id,
                    error_code="DURATION_SECONDS_IN_BEAT",
                    message=f"duration_seconds in source_beats[{idx}] (beat_id={beat.get('beat_id')!r}); durations computed by packer, not authored here",
                )
            )

    return errors


def validate_scene_beat_plan_batch(
    records: list[dict[str, Any]],
) -> dict[str, list[SceneBeatPlanValidationError]]:
    """
    Validate multiple scene_beat_plan records and collect errors by scene_id.

    Note: duplicate beat_ids are allowed across different scenes. This function
    only enforces uniqueness within each scene.

    Args:
        records: list of scene_beat_plan records

    Returns:
        Dict mapping scene_id -> list of validation errors. Empty dict if all valid.
    """
    result: dict[str, list[SceneBeatPlanValidationError]] = {}

    for record in records:
        errors = validate_scene_beat_plan(record)
        if errors:
            scene_id = record.get("scene_id", "UNKNOWN")
            result[scene_id] = errors

    return result
