"""
Deterministic duration planner for Omni coverage planning.

This module is intentionally pure: it does not read files, write records, call
external services, or mutate repository metadata. Later agents can use this
planner to turn a scene_action_type and target duration into duration slots.
"""

from __future__ import annotations

from typing import Any


SUPPORTED_TARGET_DURATIONS = (5, 10, 15)

SHOT_COUNT_BOUNDS = {
    5: (1, 2),
    10: (2, 3),
    15: (3, 5),
}

SCENE_ACTION_RULES = {
    "static_tension": {
        5: (1, "single held tension beat"),
        10: (2, "establish tension geometry, then hold the response"),
        15: (3, "establish geometry, isolate the tension cue, then hold reaction"),
    },
    "dialogue_exchange": {
        5: (2, "speaker/listener exchange with minimal coverage"),
        10: (3, "two-sided exchange with one grounding beat"),
        15: (5, "full exchange coverage with grounding, response, and hold beats"),
    },
    "discovery_or_reveal": {
        5: (1, "single reveal beat"),
        10: (3, "approach, reveal, then reaction"),
        15: (4, "approach, reveal detail, recognition, then reaction hold"),
    },
    "physical_action": {
        5: (2, "action setup and completion"),
        10: (3, "setup, action, and consequence"),
        15: (5, "setup, initiation, action detail, consequence, and recovery"),
    },
    "object_insert": {
        5: (1, "single object emphasis beat"),
        10: (2, "object context and detail insert"),
        15: (3, "object context, detail insert, and reaction"),
    },
    "arrival_or_departure": {
        5: (1, "single arrival or exit beat"),
        10: (2, "movement into or out of frame, then settle"),
        15: (4, "approach, threshold, crossing, and settle"),
    },
    "transition_or_atmosphere": {
        5: (1, "single atmosphere bridge"),
        10: (2, "atmosphere establish and transition cue"),
        15: (3, "atmosphere establish, transition detail, and settle"),
    },
}


def plan_omni_duration(
    scene_action_type: str,
    target_duration_seconds: int,
) -> dict[str, Any]:
    """Return deterministic shot-count and duration-slot guidance."""
    if target_duration_seconds not in SUPPORTED_TARGET_DURATIONS:
        supported = ", ".join(str(value) for value in SUPPORTED_TARGET_DURATIONS)
        raise ValueError(
            f"Unsupported target_duration_seconds {target_duration_seconds!r}; "
            f"expected one of: {supported}."
        )

    if scene_action_type not in SCENE_ACTION_RULES:
        supported = ", ".join(sorted(SCENE_ACTION_RULES))
        raise ValueError(
            f"Unknown scene_action_type {scene_action_type!r}; expected one of: {supported}."
        )

    min_shot_count, max_shot_count = SHOT_COUNT_BOUNDS[target_duration_seconds]
    recommended_shot_count, rhythm = SCENE_ACTION_RULES[scene_action_type][
        target_duration_seconds
    ]
    if not min_shot_count <= recommended_shot_count <= max_shot_count:
        raise ValueError(
            f"Rule table error for {scene_action_type}/{target_duration_seconds}: "
            f"recommended_shot_count {recommended_shot_count} is outside "
            f"{min_shot_count}-{max_shot_count}."
        )

    duration_slots = _duration_slots(
        target_duration_seconds=target_duration_seconds,
        shot_count=recommended_shot_count,
    )
    return {
        "scene_action_type": scene_action_type,
        "target_duration_seconds": target_duration_seconds,
        "recommended_shot_count": recommended_shot_count,
        "min_shot_count": min_shot_count,
        "max_shot_count": max_shot_count,
        "rhythm": rhythm,
        "duration_slots": duration_slots,
    }


def _duration_slots(*, target_duration_seconds: int, shot_count: int) -> list[int]:
    base = target_duration_seconds // shot_count
    remainder = target_duration_seconds % shot_count
    slots = [base + (1 if index < remainder else 0) for index in range(shot_count)]
    if any(slot < 1 for slot in slots):
        raise ValueError("Duration rule table produced a shot shorter than 1 second.")
    return slots


__all__ = [
    "SCENE_ACTION_RULES",
    "SHOT_COUNT_BOUNDS",
    "SUPPORTED_TARGET_DURATIONS",
    "plan_omni_duration",
]
