from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.storyboard_options import (  # noqa: E402
    StoryboardOptionsAgent,
    StoryboardOptionsError,
)
from scripts.validate_production_records import run_validation  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_scene(
    repo_root: Path,
    *,
    scene_id: str = "SC0001",
    visual_targets: dict | None = None,
) -> None:
    scene_dir = repo_root / "planning" / "scenes" / scene_id
    scene_dir.mkdir(parents=True)
    _write_yaml(
        scene_dir / "scene_card.yaml",
        {
            "scene_id": scene_id,
            "excerpt_ref": "scene_excerpt.md",
            "visual_targets": visual_targets
            if visual_targets is not None
            else {
                "palette": "Pale stone and muted domestic neutrals.",
                "lens_bias": "Restrained intimate coverage.",
                "framing_bias": "Thresholds, corridor depth, and doorways.",
                "movement_bias": "Minimal, exact movement.",
                "lighting_bias": "Filtered early daylight and low-key practicals.",
            },
        },
    )
    (scene_dir / "scene_excerpt.md").write_text(
        "Nadia notices the framed photograph is off by three or four degrees.",
        encoding="utf-8",
    )


def _copy_production_schemas(repo_root: Path) -> None:
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True)
    for name in (
        "image_selection.schema.json",
        "asset_clearance.schema.json",
        "storyboard_option.schema.json",
        "shot_list_omni_suggestion.schema.json",
        "batch_job.schema.json",
    ):
        (schemas_dir / name).write_text(
            (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _validate_storyboard_payload(payload: dict) -> list[str]:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "storyboard_option.schema.json").read_text(
            encoding="utf-8"
        )
    )
    return [
        f"{'.'.join(str(p) for p in error.absolute_path) or '(root)'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(payload)
    ]


def test_storyboard_options_agent_writes_metadata_only_board(tmp_path: Path) -> None:
    _write_scene(tmp_path)

    result = StoryboardOptionsAgent(tmp_path).build("SC0001")

    assert result.storyboard_options_path == (
        tmp_path / "visual_dev" / "storyboards" / "SC0001" / "storyboard_options.yaml"
    )
    assert result.storyboard_options_path.exists()
    assert not list((tmp_path / "visual_dev" / "storyboards").rglob("*.png"))
    assert not list((tmp_path / "visual_dev" / "storyboards").rglob("*.mp4"))


def test_storyboard_options_payload_passes_schema(tmp_path: Path) -> None:
    _write_scene(tmp_path)

    result = StoryboardOptionsAgent(tmp_path).build("SC0001")
    payload = _load_yaml(result.storyboard_options_path)

    assert _validate_storyboard_payload(payload) == []
    assert payload["scene_id"] == "SC0001"
    assert payload["source_refs"]["scene_card"] == "planning/scenes/SC0001/scene_card.yaml"
    assert payload["source_refs"]["scene_excerpt"] == (
        "planning/scenes/SC0001/scene_excerpt.md"
    )
    assert len(payload["options"]) >= 5
    assert payload["selected_option"] is None
    assert payload["review_status"] == "pending"
    assert payload["storage_policy"] == "no_binary_commits"


def test_storyboard_options_do_not_auto_select_or_attach_prompts(
    tmp_path: Path,
) -> None:
    _write_scene(tmp_path)

    payload = StoryboardOptionsAgent(tmp_path).build("SC0001").payload

    assert payload["selected_option"] is None
    assert all(option["status"] == "candidate" for option in payload["options"])
    assert all(option["prompt_ids"] == [] for option in payload["options"])
    assert {option["source_field"] for option in payload["options"]} == {
        "scene_card.visual_targets.palette",
        "scene_card.visual_targets.lens_bias",
        "scene_card.visual_targets.framing_bias",
        "scene_card.visual_targets.movement_bias",
        "scene_card.visual_targets.lighting_bias",
    }


def test_missing_visual_target_marks_option_evidence_thin(tmp_path: Path) -> None:
    _write_scene(
        tmp_path,
        visual_targets={
            "palette": "Pale stone and muted domestic neutrals.",
            "lens_bias": "Restrained intimate coverage.",
        },
    )

    payload = StoryboardOptionsAgent(tmp_path).build("SC0001").payload

    assert len(payload["options"]) == 5
    assert any(option["status"] == "evidence_thin" for option in payload["options"])
    assert any("EVIDENCE_THIN" in option["purpose"] for option in payload["options"])


def test_unresolved_visual_target_blocks_option(tmp_path: Path) -> None:
    _write_scene(
        tmp_path,
        visual_targets={
            "palette": "TODO_REVIEW: palette needs source confirmation.",
            "lens_bias": "Restrained intimate coverage.",
            "framing_bias": "Thresholds and doorways.",
            "movement_bias": "Minimal movement.",
            "lighting_bias": "Filtered daylight.",
        },
    )

    payload = StoryboardOptionsAgent(tmp_path).build("SC0001").payload

    assert payload["options"][0]["status"] == "blocked"


def test_missing_scene_card_escalates(tmp_path: Path) -> None:
    with pytest.raises(StoryboardOptionsError, match="Missing scene card"):
        StoryboardOptionsAgent(tmp_path).build("SC0001")


def test_production_validator_accepts_storyboard_options(tmp_path: Path) -> None:
    _copy_production_schemas(tmp_path)
    _write_scene(tmp_path)
    StoryboardOptionsAgent(tmp_path).build("SC0001")

    report = run_validation(tmp_path)

    assert report.total_files == 1
    assert report.by_record_type["storyboard_options"] == 1
    assert report.valid_files == 1
    assert report.issues == []


def test_production_validator_rejects_invalid_selected_option_format(tmp_path: Path) -> None:
    # Schema now allows null OR a valid option_id string (^SC\d{4}_SB\d{2}$).
    # An arbitrary non-conforming string must still be rejected.
    _copy_production_schemas(tmp_path)
    _write_scene(tmp_path)
    result = StoryboardOptionsAgent(tmp_path).build("SC0001")
    payload = _load_yaml(result.storyboard_options_path)
    payload["selected_option"] = "not-a-valid-option-id"
    _write_yaml(result.storyboard_options_path, payload)

    report = run_validation(tmp_path)

    assert report.invalid_files == 1
    assert any("selected_option" in issue.field_path for issue in report.issues)
