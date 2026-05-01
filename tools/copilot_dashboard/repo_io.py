"""Read-only repository loaders for the copilot dashboard."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.operator_next_step import recommend_next_step


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_yaml_record(path: Path, repo_root: Path) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(payload, dict):
        return None
    return {"record_path": _relative(path, repo_root), **payload}


def _load_recent_yaml_records(
    repo_root: Path,
    pattern: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    paths = sorted((repo_root / pattern).parent.glob(Path(pattern).name), reverse=True)
    records: list[dict[str, Any]] = []
    for path in paths:
        record = _read_yaml_record(path, repo_root)
        if record is not None:
            records.append(record)
        if len(records) >= limit:
            break
    return records


def load_recent_sessions(repo_root: str | Path, *, limit: int = 10) -> list[dict[str, Any]]:
    """Load the most recent operator session YAML records."""
    root = Path(repo_root)
    return _load_recent_yaml_records(
        root,
        "evidence/operator_sessions/OP-*.yaml",
        limit=limit,
    )


def load_recent_handoffs(repo_root: str | Path, *, limit: int = 10) -> list[dict[str, Any]]:
    """Load the most recent agent handoff YAML records."""
    root = Path(repo_root)
    return _load_recent_yaml_records(
        root,
        "evidence/agent_handoffs/HO-*.yaml",
        limit=limit,
    )


def load_status_rows(repo_root: str | Path, *, limit: int = 10) -> list[dict[str, str]]:
    """Load the last production status CSV rows."""
    root = Path(repo_root)
    path = root / "evidence" / "production_status.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[-limit:]


def load_latest_recommendation(repo_root: str | Path) -> dict[str, Any]:
    """Load the current operator recommendation as plain data."""
    return recommend_next_step(Path(repo_root)).to_dict()
