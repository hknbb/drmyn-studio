"""
Human-triggered copilot command writer.

HA-3a implements only the switch command. It writes a metadata-only agent
handoff record from the current operator recommendation and does not mutate
prompt records, scene cards, pack manifests, lifecycle fields, or binary paths.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from scripts.agents.operator_next_step import OperatorNextStep, recommend_next_step


ALLOWED_AGENTS = {
    "human_operator",
    "claude_code",
    "codex",
    "gemini_code_assist",
    "chatgpt_project",
}
ALLOWED_REASONS = {
    "limit_reached",
    "review_requested",
    "second_opinion",
    "drafting_assist",
    "manual_pickup",
    "context_too_large",
    "task_complete",
}


@dataclass(frozen=True)
class CopilotCommandResult:
    written_files: tuple[str, ...]
    next_recommendation: OperatorNextStep | None
    message: str


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _git_value(repo_root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _handoff_timestamp(value: datetime) -> str:
    return value.strftime("%Y%m%d-%H%M%S")


def _created_at(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _next_handoff_path(repo_root: Path, timestamp: str) -> Path:
    handoffs_dir = repo_root / "evidence" / "agent_handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1000):
        suffix = "" if index == 0 else f"-{index:03d}"
        path = handoffs_dir / f"HO-{timestamp}{suffix}.yaml"
        if not path.exists():
            return path
    raise RuntimeError(f"No available handoff filename for timestamp {timestamp}.")


def apply_command(
    repo_root: Path,
    *,
    command: Literal["switch"],
    target_agent: str | None = None,
    reason: str = "limit_reached",
    session_id: str | None = None,
    now: datetime | None = None,
    branch: str | None = None,
    head_sha: str | None = None,
    from_agent: str | None = None,
) -> CopilotCommandResult:
    """HA-3a: switch command writes evidence/agent_handoffs/HO-*.yaml."""
    if command != "switch":
        raise NotImplementedError("yes/no/revise are deferred to HA-3b")
    if not target_agent:
        raise ValueError("switch command requires target_agent.")
    if target_agent not in ALLOWED_AGENTS:
        raise ValueError(f"Unknown target_agent: {target_agent}")
    if reason not in ALLOWED_REASONS:
        raise ValueError(f"Unknown handoff reason: {reason}")

    source_agent = from_agent or os.environ.get("CP_AGENT_NAME") or "human_operator"
    if source_agent not in ALLOWED_AGENTS:
        raise ValueError(f"Unknown from_agent: {source_agent}")
    if source_agent == target_agent:
        raise ValueError("from_agent and target_agent must be different.")

    root = Path(repo_root)
    recommendation = recommend_next_step(root)
    timestamp_source = now or datetime.now(timezone.utc)
    timestamp = _handoff_timestamp(timestamp_source)

    if branch is None:
        branch = _git_value(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if head_sha is None:
        raw_head_sha = _git_value(root, ["rev-parse", "HEAD"])
        head_sha = raw_head_sha[:12] if raw_head_sha else None

    handoff_path = _next_handoff_path(root, timestamp)
    payload = {
        "handoff_id": handoff_path.stem,
        "created_at": _created_at(timestamp_source),
        "from_agent": source_agent,
        "to_agent": target_agent,
        "reason": reason,
        "current_task": recommendation.current_task,
        "context_files": recommendation.open_files,
        "do_steps": recommendation.do_steps,
        "expected_outputs": recommendation.expected_outputs,
        "safety_warnings": recommendation.safety_warnings,
        "status": "open",
    }
    if recommendation.scene_id is not None:
        payload["scene_id"] = recommendation.scene_id
    if session_id is not None:
        payload["session_id"] = session_id
    if branch:
        payload["branch"] = branch
    if head_sha:
        payload["head_sha"] = head_sha

    handoff_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    written = _relative(handoff_path, root)
    return CopilotCommandResult(
        written_files=(written,),
        next_recommendation=recommendation,
        message=f"Handoff written. Paste this path to your next agent: {written}",
    )
