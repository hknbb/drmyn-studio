from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.omni_duration_planner import (  # noqa: E402
    SCENE_ACTION_RULES,
    SUPPORTED_TARGET_DURATIONS,
    plan_omni_duration,
)


def _assert_duration_invariants(plan: dict[str, object]) -> None:
    duration_slots = plan["duration_slots"]
    assert isinstance(duration_slots, list)
    assert all(isinstance(slot, int) for slot in duration_slots)
    assert all(slot >= 1 for slot in duration_slots)
    assert sum(duration_slots) == plan["target_duration_seconds"]
    assert len(duration_slots) == plan["recommended_shot_count"]
    assert plan["min_shot_count"] <= plan["recommended_shot_count"] <= plan["max_shot_count"]


@pytest.mark.parametrize(
    ("target_duration_seconds", "expected_shot_count"),
    [(5, 1), (10, 2), (15, 3)],
)
def test_static_tension_counts(
    target_duration_seconds: int,
    expected_shot_count: int,
) -> None:
    plan = plan_omni_duration("static_tension", target_duration_seconds)

    assert plan["recommended_shot_count"] == expected_shot_count
    _assert_duration_invariants(plan)


@pytest.mark.parametrize(
    ("target_duration_seconds", "expected_shot_count"),
    [(5, 2), (10, 3), (15, 5)],
)
def test_dialogue_exchange_counts(
    target_duration_seconds: int,
    expected_shot_count: int,
) -> None:
    plan = plan_omni_duration("dialogue_exchange", target_duration_seconds)

    assert plan["recommended_shot_count"] == expected_shot_count
    _assert_duration_invariants(plan)


def test_discovery_or_reveal_15s_uses_four_or_five_shots() -> None:
    plan = plan_omni_duration("discovery_or_reveal", 15)

    assert plan["recommended_shot_count"] in {4, 5}
    _assert_duration_invariants(plan)


def test_physical_action_15s_uses_five_shots() -> None:
    plan = plan_omni_duration("physical_action", 15)

    assert plan["recommended_shot_count"] == 5
    _assert_duration_invariants(plan)


def test_object_insert_5s_uses_one_shot() -> None:
    plan = plan_omni_duration("object_insert", 5)

    assert plan["recommended_shot_count"] == 1
    _assert_duration_invariants(plan)


def test_all_supported_scene_action_types_and_durations_preserve_invariants() -> None:
    for scene_action_type in SCENE_ACTION_RULES:
        for target_duration_seconds in SUPPORTED_TARGET_DURATIONS:
            plan = plan_omni_duration(scene_action_type, target_duration_seconds)
            assert plan["scene_action_type"] == scene_action_type
            assert plan["target_duration_seconds"] == target_duration_seconds
            assert isinstance(plan["rhythm"], str)
            assert plan["rhythm"]
            _assert_duration_invariants(plan)


def test_unsupported_target_duration_raises_clear_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported target_duration_seconds"):
        plan_omni_duration("static_tension", 12)


def test_unknown_scene_action_type_raises_clear_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown scene_action_type"):
        plan_omni_duration("musical_number", 10)
