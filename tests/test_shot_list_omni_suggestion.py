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


def _storyboard_options(selected_option: str | None = "SC0001_SB01") -> dict:
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
) -> Path:
    path = repo_root / "visual_dev" / "storyboards" / "SC0001" / "storyboard_options.yaml"
    _write_yaml(path, _storyboard_options(selected_option))
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

    result = ShotListOmniSuggestionAgent(tmp_path).build("SC0001")

    payload = yaml.safe_load(result.suggestion_path.read_text(encoding="utf-8"))
    assert _validate_suggestion_payload(payload) == []
    assert payload["scene_id"] == "SC0001"
    assert payload["source_storyboard_option"] == "SC0001_SB01"
    assert payload["applied_to_scene_card"] is False
    assert payload["applied_at"] is None
    assert payload["review_status"] == "pending"
    assert payload["storage_policy"] == "no_binary_commits"
    assert scene_card.read_text(encoding="utf-8") == before_scene_card
    assert storyboard_options.read_text(encoding="utf-8") == before_storyboard_options


def test_selected_option_mismatch_fails_validation_safely(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    _write_storyboard_options(tmp_path, selected_option="SC0001_SB99")

    with pytest.raises(ShotListOmniSuggestionError, match="does not match"):
        ShotListOmniSuggestionAgent(tmp_path).build("SC0001")

    assert not list(tmp_path.rglob("shot_list_omni_suggestion.yaml"))


def test_run_pipeline_mode_writes_suggestion(tmp_path: Path) -> None:
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
        ]
    )

    assert code == 0
    assert (
        tmp_path / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml"
    ).exists()


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
    _write_yaml(
        tmp_path / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml",
        {
            "scene_id": "SC0001",
            "source_storyboard_option": "SC0001_SB01",
            "source_refs": {
                "storyboard_options": "visual_dev/storyboards/SC0001/storyboard_options.yaml",
                "scene_card": "planning/scenes/SC0001/scene_card.yaml",
                "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
            },
            "suggested_shot_list": [
                {
                    "shot_id": "SC0001_OMNI01",
                    "type": "single_omni_shot",
                    "subject": "Source-grounded selected option.",
                    "camera_angle": "Static close coverage.",
                    "framing": "Doorway threshold geometry.",
                    "camera_movement": "Minimal forward drift.",
                    "duration_seconds": 5,
                    "source_field": "scene_card.visual_targets.framing_bias",
                    "source_option_field": "options[0]",
                    "notes": "Lighting: soft morning daylight.",
                }
            ],
            "suggested_by": "storyboard_agent",
            "applied_to_scene_card": False,
            "applied_at": None,
            "review_status": "pending",
            "storage_policy": "no_binary_commits",
        },
    )

    report = run_validation(tmp_path)

    assert report.total_files == 1
    assert report.valid_files == 1
    assert report.by_record_type["shot_list_omni_suggestion"] == 1
    assert report.issues == []


def test_production_validator_rejects_applied_suggestion(tmp_path: Path) -> None:
    _copy_production_schemas(tmp_path)
    payload = {
        "scene_id": "SC0001",
        "source_storyboard_option": "SC0001_SB01",
        "source_refs": {
            "storyboard_options": "visual_dev/storyboards/SC0001/storyboard_options.yaml",
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
        },
        "suggested_shot_list": [
            {
                "shot_id": "SC0001_OMNI01",
                "type": "single_omni_shot",
                "subject": "Source-grounded selected option.",
                "camera_angle": "Static close coverage.",
                "framing": "Doorway threshold geometry.",
                "camera_movement": "Minimal forward drift.",
                "duration_seconds": 5,
                "source_field": "scene_card.visual_targets.framing_bias",
                "source_option_field": "options[0]",
                "notes": "Lighting: soft morning daylight.",
            }
        ],
        "suggested_by": "storyboard_agent",
        "applied_to_scene_card": True,
        "applied_at": None,
        "review_status": "pending",
        "storage_policy": "no_binary_commits",
    }
    _write_yaml(
        tmp_path / "visual_dev/storyboards/SC0001/shot_list_omni_suggestion.yaml",
        payload,
    )

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
