from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents import run_pipeline  # noqa: E402


PROMPT_ID = "SC0001__t2i-char-c01-midjourney__v01"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_scene(repo_root: Path, scene_id: str = "SC0001") -> None:
    scene_dir = repo_root / "planning" / "scenes" / scene_id
    _write_yaml(
        scene_dir / "scene_card.yaml",
        {
            "scene_id": scene_id,
            "excerpt_ref": "scene_excerpt.md",
            "visual_targets": {
                "palette": "Muted domestic neutrals.",
                "lens_bias": "Static close coverage.",
                "framing_bias": "Doorway threshold geometry.",
                "movement_bias": "Minimal movement.",
                "lighting_bias": "Soft morning daylight.",
            },
        },
    )
    (scene_dir / "scene_excerpt.md").write_text("Scene excerpt.", encoding="utf-8")


def test_operator_next_step_mode_returns_blocked_on_empty_repo(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = run_pipeline.main(
        ["--repo-root", str(tmp_path), "--mode", "operator-next-step"]
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "current_task: blocked" in output
    assert "No production status rows" in output


def test_generate_storyboard_options_writes_null_selected_option(
    tmp_path: Path,
) -> None:
    _write_scene(tmp_path)

    code = run_pipeline.main(
        [
            "--repo-root",
            str(tmp_path),
            "--mode",
            "generate-storyboard-options",
            "--scene-id",
            "SC0001",
        ]
    )

    path = tmp_path / "visual_dev" / "storyboards" / "SC0001" / "storyboard_options.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["selected_option"] is None
    assert len(payload["options"]) == 5


def test_refresh_model_guidance_writes_placeholder_snapshot(tmp_path: Path) -> None:
    code = run_pipeline.main(
        [
            "--repo-root",
            str(tmp_path),
            "--mode",
            "refresh-model-guidance",
            "--models",
            "midjourney",
            "--save-snapshot",
        ]
    )

    snapshots = list((tmp_path / "evidence/model_guidance_snapshots").glob("*_midjourney.yaml"))
    assert code == 0
    assert len(snapshots) == 1
    payload = yaml.safe_load(snapshots[0].read_text(encoding="utf-8"))
    assert payload["model_id"] == "midjourney"
    assert payload["confidence"] == "low"
    assert payload["sources"][0]["human_verified"] is False
    assert "PLACEHOLDER" in payload["extracted_rules"][0]


def test_review_outputs_writes_metadata_without_copying_binaries_or_pack_manifest(
    tmp_path: Path,
) -> None:
    pack_manifest = tmp_path / "visual_dev/elements/characters/C01/pack_manifest.yaml"
    _write_yaml(
        pack_manifest,
        {
            "element_id": "C01",
            "pack_status": "metadata_only",
            "approved": False,
            "locked": False,
        },
    )
    before_pack_manifest = pack_manifest.read_text(encoding="utf-8")
    candidate = tmp_path / "visual_dev/elements/characters/C01/candidates/candidate_01.jpg"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"candidate placeholder")
    notes = tmp_path / "evidence/prompt_reviews" / f"{PROMPT_ID}_review.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("Human review notes.", encoding="utf-8")
    images_before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*.jpg"))

    code = run_pipeline.main(
        [
            "--repo-root",
            str(tmp_path),
            "--mode",
            "review-outputs",
            "--prompt-id",
            PROMPT_ID,
            "--images",
            "visual_dev/elements/characters/C01/candidates",
            "--review-notes",
            f"evidence/prompt_reviews/{PROMPT_ID}_review.md",
        ]
    )

    images_after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*.jpg"))
    selection_path = tmp_path / "visual_dev/elements/characters/C01/image_selection.yaml"
    suggestion_path = (
        tmp_path
        / "visual_dev/elements/characters/C01/pack_manifest_update_suggestion.yaml"
    )
    assert code == 0
    assert selection_path.exists()
    assert suggestion_path.exists()
    assert images_after == images_before
    assert pack_manifest.read_text(encoding="utf-8") == before_pack_manifest


def test_invalid_clip_locking_mode_fails_cleanly(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run_pipeline.main(
            [
                "--repo-root",
                str(tmp_path),
                "--mode",
                "lock-scene-clip",
            ]
        )

    assert exc.value.code == 2
