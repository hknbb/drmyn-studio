from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.graph import run_graph  # noqa: E402
from scripts.agents.run_pipeline import main as run_pipeline_main  # noqa: E402
from scripts.agents.shot_list_omni_suggestion import (  # noqa: E402
    ShotListOmniSuggestionAgent,
    ShotListOmniSuggestionError,
)
from scripts.agents.state import PipelineState  # noqa: E402
from scripts.validate_production_records import run_validation  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_scene(repo_root: Path, scene_id: str = "SC0001") -> Path:
    scene_dir = repo_root / "planning" / "scenes" / scene_id
    scene_card = scene_dir / "scene_card.yaml"
    _write_yaml(
        scene_card,
        {
            "scene_id": scene_id,
            "excerpt_ref": "scene_excerpt.md",
            "shot_list_omni": [],
        },
    )
    (scene_dir / "scene_excerpt.md").write_text("Scene excerpt.", encoding="utf-8")
    return scene_card


def _coverage_shots() -> list[dict]:
    return [
        {
            "role": "establish_coverage",
            "subject": "Establish the doorway threshold geometry.",
            "camera_angle": "Static close coverage at the doorway.",
            "framing": "Doorway threshold geometry with restrained depth.",
            "camera_movement": "Minimal forward drift.",
            "lighting": "Soft morning daylight.",
            "min_duration_seconds": 1,
            "max_duration_seconds": 5,
            "source_field": "scene_card.visual_targets.framing_bias",
        },
        {
            "role": "action_or_deviation_coverage",
            "subject": "Register the source-stated object deviation.",
            "camera_angle": "Static close coverage at the doorway.",
            "framing": "Doorway threshold geometry with restrained depth.",
            "camera_movement": "Minimal forward drift.",
            "lighting": "Soft morning daylight.",
            "min_duration_seconds": 1,
            "max_duration_seconds": 5,
            "source_field": "scene_card.visual_targets.framing_bias",
        },
        {
            "role": "reaction_or_hold_coverage",
            "subject": "Hold the source-grounded response.",
            "camera_angle": "Static close coverage at the doorway.",
            "framing": "Doorway threshold geometry with restrained depth.",
            "camera_movement": "Minimal forward drift.",
            "lighting": "Soft morning daylight.",
            "min_duration_seconds": 1,
            "max_duration_seconds": 5,
            "source_field": "scene_card.visual_targets.framing_bias",
        },
    ]


def _storyboard_options(
    selected_option: str | None = "SC0001_SB01",
    *,
    scene_action_type: str = "static_tension",
) -> dict:
    return {
        "scene_id": "SC0001",
        "round": 1,
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
        },
        "options": [
            {
                "option_id": f"SC0001_SB{index:02d}",
                "purpose": "Represent the source-stated threshold composition.",
                "coverage_strategy": "threshold_geometry_coverage",
                "scene_action_type": scene_action_type,
                "coverage_shots": _coverage_shots(),
                "camera_angle": "Static close coverage at the doorway.",
                "framing": "Doorway threshold geometry with restrained depth.",
                "movement": "Minimal forward drift.",
                "lighting": "Soft morning daylight.",
                "source_field": "scene_card.visual_targets.framing_bias",
                "prompt_ids": [],
                "status": "candidate",
            }
            for index in range(1, 6)
        ],
        "selected_option": selected_option,
        "review_status": "pending",
        "storage_policy": "no_binary_commits",
    }


def _write_storyboard_options(
    repo_root: Path,
    selected_option: str | None = "SC0001_SB01",
    *,
    scene_action_type: str = "static_tension",
) -> Path:
    path = repo_root / "visual_dev" / "storyboards" / "SC0001" / "storyboard_options.yaml"
    _write_yaml(path, _storyboard_options(selected_option, scene_action_type=scene_action_type))
    return path


def _copy_production_schemas(repo_root: Path) -> None:
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True)
    for name in (
        "image_selection.schema.json",
        "asset_clearance.schema.json",
        "storyboard_option.schema.json",
        "shot_list_omni_suggestion.schema.json",
        "batch_job.schema.json",
        "operator_session.schema.json",
    ):
        (schemas_dir / name).write_text(
            (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _validate_suggestion_payload(payload: dict) -> list[str]:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "shot_list_omni_suggestion.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(payload)]


def _assert_duration_invariants(payload: dict) -> None:
    shots = payload["suggested_shot_list"]
    durations = [shot["duration_seconds"] for shot in shots]
    assert sum(durations) == payload["target_duration_seconds"]
    assert all(duration >= 1 for duration in durations)
    assert len(shots) == payload["duration_plan"]["recommended_shot_count"]
    assert payload["duration_plan"]["duration_slots"] == durations


def test_selected_option_null_blocks_without_writing_suggestion(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path, selected_option=None)

    with pytest.raises(ShotListOmniSuggestionError, match="selected_option"):
        ShotListOmniSuggestionAgent(tmp_path).build("SC0001")

    assert not (
        tmp_path / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml"
    ).exists()


def test_valid_selected_option_writes_schema_valid_suggestion(tmp_path: Path) -> None:
    scene_card = _write_scene(tmp_path)
    storyboard_options = _write_storyboard_options(tmp_path)
    before_scene_card = scene_card.read_text(encoding="utf-8")
    before_storyboard_options = storyboard_options.read_text(encoding="utf-8")

    result = ShotListOmniSuggestionAgent(tmp_path).build(
        "SC0001",
        target_duration_seconds=15,
    )

    payload = yaml.safe_load(result.suggestion_path.read_text(encoding="utf-8"))
    assert _validate_suggestion_payload(payload) == []
    assert payload["scene_id"] == "SC0001"
    assert payload["source_selected_option"] == "SC0001_SB01"
    assert payload["source_storyboard_options"] == (
        "visual_dev/storyboards/SC0001/storyboard_options.yaml"
    )
    assert payload["target_duration_seconds"] == 15
    assert payload["coverage_strategy"] == "threshold_geometry_coverage"
    assert payload["scene_action_type"] == "static_tension"
    assert payload["applied_to_scene_card"] is False
    assert payload["applied_at"] is None
    assert payload["review_status"] == "pending"
    assert payload["storage_policy"] == "no_binary_commits"
    _assert_duration_invariants(payload)
    assert scene_card.read_text(encoding="utf-8") == before_scene_card
    assert storyboard_options.read_text(encoding="utf-8") == before_storyboard_options


def test_selected_option_mismatch_fails_validation_safely(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path, selected_option="SC0001_SB99")

    with pytest.raises(ShotListOmniSuggestionError, match="does not match"):
        ShotListOmniSuggestionAgent(tmp_path).build("SC0001")

    assert not list(tmp_path.rglob("shot_list_omni_suggestion.yaml"))


def test_unsupported_target_duration_fails_without_writing(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)

    with pytest.raises(ShotListOmniSuggestionError, match="Unsupported"):
        ShotListOmniSuggestionAgent(tmp_path).build(
            "SC0001",
            target_duration_seconds=12,
        )

    assert not list(tmp_path.rglob("shot_list_omni_suggestion.yaml"))


@pytest.mark.parametrize(
    ("target_duration_seconds", "min_shots", "max_shots"),
    [(5, 1, 2), (10, 2, 3), (15, 3, 5)],
)
def test_target_duration_controls_shot_count(
    tmp_path: Path,
    target_duration_seconds: int,
    min_shots: int,
    max_shots: int,
) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path, scene_action_type="dialogue_exchange")

    payload = ShotListOmniSuggestionAgent(tmp_path).build(
        "SC0001",
        target_duration_seconds=target_duration_seconds,
        write=False,
    ).payload

    assert min_shots <= len(payload["suggested_shot_list"]) <= max_shots
    _assert_duration_invariants(payload)


def test_run_pipeline_mode_writes_suggestion_with_target_duration(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)

    code = run_pipeline_main(
        [
            "--repo-root",
            str(tmp_path),
            "--mode",
            "generate-shot-list-omni-suggestion",
            "--scene-id",
            "SC0001",
            "--target-duration-seconds",
            "15",
        ]
    )

    path = tmp_path / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["target_duration_seconds"] == 15


def test_graph_mode_wraps_suggestion_without_new_logic(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)

    result = run_graph(
        PipelineState(
            repo_root=str(tmp_path),
            mode="generate-shot-list-omni-suggestion",
            scene_ids=["SC0001"],
        )
    )

    assert result.errors == []
    assert "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml" in (
        result.written_files
    )


def test_production_validator_accepts_valid_suggestion(tmp_path: Path) -> None:
    _copy_production_schemas(tmp_path)
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)
    ShotListOmniSuggestionAgent(tmp_path).build("SC0001", target_duration_seconds=15)

    report = run_validation(tmp_path)

    assert report.total_files == 2
    assert report.valid_files == 2
    assert report.by_record_type["shot_list_omni_suggestion"] == 1
    assert report.issues == []


def test_production_validator_rejects_applied_suggestion(tmp_path: Path) -> None:
    _copy_production_schemas(tmp_path)
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)
    result = ShotListOmniSuggestionAgent(tmp_path).build(
        "SC0001",
        target_duration_seconds=15,
    )
    payload = result.payload
    payload["applied_to_scene_card"] = True
    _write_yaml(result.suggestion_path, payload)

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any(
        issue.record_type == "shot_list_omni_suggestion"
        and issue.field_path == "applied_to_scene_card"
        for issue in report.issues
    )


def test_no_binaries_or_video_records_are_created(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path)

    ShotListOmniSuggestionAgent(tmp_path).build("SC0001")

    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.jpg"))
    assert not list(tmp_path.rglob("*.mp4"))
    assert not list(tmp_path.rglob("video_takes.yaml"))
    assert not list(tmp_path.rglob("selected_take.yaml"))
    assert not (tmp_path / "evidence/scene_clip_map.csv").exists()


def test_sc0001_repo_suggestion_uses_selected_sb03_and_target_15() -> None:
    path = REPO_ROOT / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert payload["source_selected_option"] == "SC0001_SB03"
    assert payload["target_duration_seconds"] == 15
    assert payload["scene_action_type"] == "static_tension"
    assert payload["coverage_strategy"] == "threshold_geometry_coverage"
    assert payload["applied_to_scene_card"] is False
    assert payload["storage_policy"] == "no_binary_commits"
    assert "night" not in yaml.safe_dump(payload).lower()
    assert "sodium" not in yaml.safe_dump(payload).lower()
    _assert_duration_invariants(payload)
