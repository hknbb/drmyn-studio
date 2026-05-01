from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.copilot_dashboard import repo_io  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_load_recent_sessions_returns_newest_records_with_paths(tmp_path: Path) -> None:
    for index in range(12):
        _write_yaml(
            tmp_path / "evidence/operator_sessions" / f"OP-20260501-1200{index:02d}.yaml",
            {
                "session_id": f"OP-20260501-1200{index:02d}",
                "created_at": "2026-05-01T12:00:00Z",
                "scene_id": None,
                "current_task": f"task_{index}",
                "recommended_files": [],
                "recommended_steps": ["Review current task."],
                "status": "in_progress",
                "notes": "",
            },
        )

    records = repo_io.load_recent_sessions(tmp_path)

    assert len(records) == 10
    assert records[0]["session_id"] == "OP-20260501-120011"
    assert records[-1]["session_id"] == "OP-20260501-120002"
    assert records[0]["record_path"] == (
        "evidence/operator_sessions/OP-20260501-120011.yaml"
    )


def test_load_recent_handoffs_skips_non_mapping_yaml(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "evidence/agent_handoffs/HO-20260501-120000.yaml",
        {
            "handoff_id": "HO-20260501-120000",
            "created_at": "2026-05-01T12:00:00Z",
            "from_agent": "codex",
            "to_agent": "claude_code",
            "reason": "manual_pickup",
            "current_task": "dashboard_viewer",
            "context_files": ["tools/copilot_dashboard/repo_io.py"],
            "do_steps": ["Inspect dashboard data."],
            "expected_outputs": ["Read-only dashboard."],
            "safety_warnings": [],
            "status": "open",
        },
    )
    bad_path = tmp_path / "evidence/agent_handoffs/HO-20260501-120001.yaml"
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    records = repo_io.load_recent_handoffs(tmp_path)

    assert len(records) == 1
    assert records[0]["handoff_id"] == "HO-20260501-120000"
    assert records[0]["record_path"] == (
        "evidence/agent_handoffs/HO-20260501-120000.yaml"
    )


def test_load_status_rows_returns_last_ten_rows(tmp_path: Path) -> None:
    path = tmp_path / "evidence/production_status.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scene_id", "overall_status"])
        writer.writeheader()
        for index in range(12):
            writer.writerow(
                {
                    "scene_id": f"SC{index:04d}",
                    "overall_status": f"status_{index}",
                }
            )

    rows = repo_io.load_status_rows(tmp_path)

    assert len(rows) == 10
    assert rows[0]["scene_id"] == "SC0002"
    assert rows[-1]["scene_id"] == "SC0011"


def test_load_latest_recommendation_is_plain_dict(tmp_path: Path) -> None:
    recommendation = repo_io.load_latest_recommendation(tmp_path)

    assert recommendation["current_task"] == "blocked"
    assert recommendation["allowed_commands"] == ("switch",)
    assert "blocked_reason" in recommendation
