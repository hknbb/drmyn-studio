from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.adapters.kling_omni import KlingOmniAdapter  # noqa: E402


def _read_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_kling_matrix_matches_active_guide_capabilities() -> None:
    matrix = _read_yaml(REPO_ROOT / "docs/model_guides/model_capability_matrix.yaml")
    guide = _read_yaml(REPO_ROOT / "docs/model_guides/kling_omni.yaml")

    kling_matrix = matrix["models"]["kling_omni"]
    kling_capability = guide["capability"]

    for field in (
        "supports_negative_prompt",
        "supports_multi_shot",
        "supports_audio",
        "max_duration_seconds",
    ):
        assert kling_matrix[field] == kling_capability[field]

    assert guide["prompt_rules"]["style"] == "cinematic_direction_spec"
    assert kling_matrix["prompt_style"] == guide["prompt_rules"]["style"]


def test_kling_adapter_max_duration_resolves_to_matrix_value() -> None:
    assert KlingOmniAdapter(REPO_ROOT)._max_duration_seconds() == 15


def test_run_costs_csv_has_unique_run_ids() -> None:
    rows = _read_csv(REPO_ROOT / "evidence/run_costs.csv")
    run_ids = [row["run_id"] for row in rows]

    assert len(run_ids) == len(set(run_ids))


def test_scene_prompt_map_has_unique_scene_prompt_model_keys() -> None:
    rows = _read_csv(REPO_ROOT / "evidence/scene_prompt_map.csv")
    keys = [
        (row["scene_id"], row["prompt_id"], row["target_model"])
        for row in rows
    ]

    assert len(keys) == len(set(keys))
