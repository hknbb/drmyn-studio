from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.copilot_dashboard import review_panels  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _quality_scores() -> dict[str, int]:
    return {
        "identity_consistency": 4,
        "source_grounding": 4,
        "style_compliance": 4,
        "continuity": 4,
        "production_usability": 4,
    }


def test_image_candidate_loader_handles_missing_files(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    rows = review_panels.load_image_candidate_rows(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert rows == []
    assert after == before


def test_video_take_loader_handles_missing_files(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    rows = review_panels.load_video_take_rows(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert rows == []
    assert after == before


def test_image_candidate_refs_are_text_metadata_only(tmp_path: Path) -> None:
    selection_path = (
        tmp_path
        / "visual_dev"
        / "elements"
        / "characters"
        / "C01"
        / "image_selection.yaml"
    )
    _write_yaml(
        selection_path,
        {
            "element_id": "C01",
            "element_type": "character",
            "selection_round": 1,
            "source_prompt_ids": ["SC0001__nadia-portrait__v01"],
            "candidate_images": [
                {
                    "asset_id": "nadia_001",
                    "path": "local://ClosingPriceMedia/elements/C01/nadia_001.png",
                    "external_storage_ref": "gdrive://ClosingPriceMedia/elements/C01/nadia_001.png",
                    "repo_binary_committed": False,
                    "status": "candidate",
                    "reason": "Candidate pending human review.",
                    "quality_scores": _quality_scores(),
                    "failure_reason": None,
                }
            ],
            "canonical_images": [],
            "round_status": "in_progress",
            "pack_manifest_sync": "pending",
        },
    )
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    rows = review_panels.load_image_candidate_rows(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before
    assert len(rows) == 1
    assert rows[0]["path_kind"] == "local_manual"
    assert rows[0]["path_display"] == "text"
    assert rows[0]["path_exists_in_repo"] is False
    assert rows[0]["external_storage_kind"] == "gdrive_manual"
    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.jpg"))


def test_video_take_refs_are_text_metadata_only(tmp_path: Path) -> None:
    takes_path = tmp_path / "visual_dev" / "omni_sets" / "SC0001" / "video_takes.yaml"
    _write_yaml(
        takes_path,
        {
            "scene_id": "SC0001",
            "prompt_id": "SC0001__kitchen-passage__v01",
            "takes": [
                {
                    "take_id": "SC0001_TAKE001",
                    "platform_asset_ref": "kling://asset/123",
                    "external_storage_ref": "gdrive://ClosingPriceMedia/video/SC0001/take001.mp4",
                    "local_proxy_ref": "local://ClosingPriceMedia/proxies/SC0001/take001.mp4",
                    "repo_binary_committed": False,
                    "storage_status": "stored_external",
                    "status": "candidate",
                    "reason": "Pending operator review.",
                    "quality_scores": _quality_scores(),
                    "failure_reason": None,
                }
            ],
            "selected_take": None,
            "round_status": "in_progress",
            "needs_prompt_revision": False,
            "storage_policy": "external_video_only",
        },
    )
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    rows = review_panels.load_video_take_rows(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before
    assert len(rows) == 1
    assert rows[0]["external_storage_kind"] == "gdrive_manual"
    assert rows[0]["local_proxy_kind"] == "local_manual"
    assert rows[0]["local_proxy_display"] == "text"
    assert rows[0]["local_proxy_exists_in_repo"] is False
    assert not list(tmp_path.rglob("*.mp4"))
    assert not list(tmp_path.rglob("*.mov"))


def test_review_panel_data_combines_read_only_rows(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "visual_dev" / "omni_sets" / "SC0001" / "video_takes.yaml",
        {
            "scene_id": "SC0001",
            "prompt_id": "SC0001__kitchen-passage__v01",
            "takes": [],
            "selected_take": None,
            "round_status": "in_progress",
            "needs_prompt_revision": False,
            "storage_policy": "external_video_only",
        },
    )

    data = review_panels.load_review_panel_data(tmp_path)

    assert data == {"image_candidates": [], "video_takes": []}
