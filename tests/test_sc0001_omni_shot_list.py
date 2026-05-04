from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENE_CARD_PATH = REPO_ROOT / "planning" / "scenes" / "SC0001" / "scene_card.yaml"
SUGGESTION_PATH = (
    REPO_ROOT / "visual_dev" / "storyboards" / "SC0001" / "shot_list_omni_suggestion.yaml"
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_sc0001_scene_card_has_applied_omni_shot_list() -> None:
    card = _load_yaml(SCENE_CARD_PATH)
    shot_list = card["shot_list_omni"]

    assert card["time_of_day"] == "MORNING"
    assert card["time_of_day_text_raw"] == "EARLY MORNING"
    assert len(shot_list) == 3
    assert [shot["shot_id"] for shot in shot_list] == [
        "SC0001_OMNI01",
        "SC0001_OMNI02",
        "SC0001_OMNI03",
    ]
    assert [shot["duration_seconds"] for shot in shot_list] == [5, 5, 5]
    assert sum(shot["duration_seconds"] for shot in shot_list) == 15
    assert all(isinstance(shot["duration_seconds"], int) for shot in shot_list)
    assert all(shot["duration_seconds"] > 0 for shot in shot_list)
    assert all(shot["source_storyboard_option"] == "SC0001_SB03" for shot in shot_list)


def test_sc0001_omni_shot_list_preserves_morning_lighting_lock() -> None:
    card = _load_yaml(SCENE_CARD_PATH)
    shot_list_text = yaml.safe_dump(card["shot_list_omni"], sort_keys=False)
    lower_text = shot_list_text.lower()

    assert "filtered early daylight" in lower_text
    assert "low-key interior practicals" in lower_text
    assert "muted domestic neutrals" in card["visual_targets"]["palette"].lower()
    assert "night" not in lower_text
    assert "sodium" not in lower_text


def test_sc0001_suggestion_marked_applied_without_lifecycle_promotion() -> None:
    suggestion = _load_yaml(SUGGESTION_PATH)

    assert suggestion["source_selected_option"] == "SC0001_SB03"
    assert suggestion["target_duration_seconds"] == 15
    assert suggestion["applied_to_scene_card"] is True
    assert suggestion["applied_at"] == "2026-05-04T18:45:00Z"
    assert suggestion["review_status"] == "pending"
    assert suggestion["storage_policy"] == "no_binary_commits"


def test_sc0001_scene_card_and_suggestion_pass_schemas() -> None:
    scene_schema = json.loads(
        (REPO_ROOT / "schemas" / "scene_card.schema.json").read_text(encoding="utf-8")
    )
    suggestion_schema = json.loads(
        (REPO_ROOT / "schemas" / "shot_list_omni_suggestion.schema.json").read_text(
            encoding="utf-8"
        )
    )

    scene_errors = [
        error.message
        for error in Draft202012Validator(scene_schema).iter_errors(
            _load_yaml(SCENE_CARD_PATH)
        )
    ]
    suggestion_errors = [
        error.message
        for error in Draft202012Validator(suggestion_schema).iter_errors(
            _load_yaml(SUGGESTION_PATH)
        )
    ]

    assert scene_errors == []
    assert suggestion_errors == []


def test_sc0001_b5_creates_no_binary_outputs() -> None:
    binary_suffixes = {".png", ".jpg", ".jpeg", ".mp4", ".mov"}
    paths = [
        path
        for root in ("visual_dev", "evidence")
        for path in (REPO_ROOT / root).rglob("*")
        if path.suffix.lower() in binary_suffixes
    ]

    assert paths == []
