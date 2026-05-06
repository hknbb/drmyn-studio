"""
Human-triggered copilot command writer.

Writes metadata-only copilot command records from the current operator
recommendation. It does not mutate prompt records, scene cards, pack manifests,
lifecycle fields, or binary paths.
"""

from __future__ import annotations

import os
import re
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
COMMANDS = {"yes", "no", "revise", "switch"}
PROMPT_RELATED_TASKS = {
    "t2i_image_generation",
    "image_review_preparation",
    "image_review",
    "model_guidance_snapshot_refresh",
}
PROMPT_ID_RE = re.compile(r"SC\d{4}__[A-Za-z0-9_.-]+__v\d{2}")


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


def _next_operator_session_path(repo_root: Path, timestamp: str) -> Path:
    sessions_dir = repo_root / "evidence" / "operator_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1000):
        suffix = "" if index == 0 else f"-{index:03d}"
        path = sessions_dir / f"OP-{timestamp}{suffix}.yaml"
        if not path.exists():
            return path
    raise RuntimeError(f"No available operator session filename for {timestamp}.")


def _next_revision_path(repo_root: Path, timestamp: str) -> Path:
    sessions_dir = repo_root / "evidence" / "operator_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1000):
        suffix = "" if index == 0 else f"-{index:03d}"
        path = sessions_dir / f"OP-{timestamp}{suffix}_revisions.md"
        if not path.exists():
            return path
    raise RuntimeError(f"No available revision filename for {timestamp}.")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _operator_session_payload(
    *,
    path: Path,
    created_at: str,
    recommendation: OperatorNextStep,
    status: str,
    notes: str,
) -> dict:
    return {
        "session_id": path.stem,
        "created_at": created_at,
        "scene_id": recommendation.scene_id,
        "current_task": recommendation.current_task,
        "recommended_files": recommendation.open_files,
        "recommended_steps": recommendation.do_steps,
        "status": status,
        "notes": notes,
    }


def _prompt_id_from_recommendation(recommendation: OperatorNextStep) -> str | None:
    for item in recommendation.open_files:
        match = PROMPT_ID_RE.search(item)
        if match:
            return match.group(0)
    return None


def _write_operator_session(
    repo_root: Path,
    *,
    recommendation: OperatorNextStep,
    timestamp: str,
    created_at: str,
    status: str,
    notes: str,
) -> str:
    path = _next_operator_session_path(repo_root, timestamp)
    payload = _operator_session_payload(
        path=path,
        created_at=created_at,
        recommendation=recommendation,
        status=status,
        notes=notes,
    )
    _write_yaml(path, payload)
    return _relative(path, repo_root)


def _write_prompt_revision_brief(
    repo_root: Path,
    *,
    recommendation: OperatorNextStep,
    note: str,
) -> str:
    prompt_id = _prompt_id_from_recommendation(recommendation)
    if prompt_id is None:
        raise ValueError("revise requires a prompt id in the current recommendation.")
    path = repo_root / "evidence" / "prompt_reviews" / f"{prompt_id}_brief.yaml"
    payload = {
        "source_prompt_id": prompt_id,
        "corrected_brief": {
            "revision_reason": note,
            "operator_current_task": recommendation.current_task,
            "recommended_files": recommendation.open_files,
            "recommended_steps": recommendation.do_steps,
        },
    }
    _write_yaml(path, payload)
    return _relative(path, repo_root)


def _write_revision_markdown(
    repo_root: Path,
    *,
    recommendation: OperatorNextStep,
    timestamp: str,
    created_at: str,
    note: str,
) -> str:
    path = _next_revision_path(repo_root, timestamp)
    lines = [
        f"# Operator Revision {path.stem}",
        "",
        f"- created_at: {created_at}",
        f"- current_task: {recommendation.current_task}",
        f"- scene_id: {recommendation.scene_id or 'none'}",
        "",
        "## Note",
        "",
        note,
        "",
        "## Recommended Files",
        "",
        *[f"- `{item}`" for item in recommendation.open_files],
        "",
        "## Recommended Steps",
        "",
        *[f"- {item}" for item in recommendation.do_steps],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return _relative(path, repo_root)


def _write_handoff_record(
    repo_root: Path,
    *,
    recommendation: OperatorNextStep,
    target_agent: str,
    reason: str,
    timestamp: str,
    created_at: str,
    from_agent: str,
    session_id: str | None,
    branch: str | None,
    head_sha: str | None,
) -> str:
    """Write one HO-*.yaml and return its repo-relative path."""
    handoff_path = _next_handoff_path(repo_root, timestamp)
    payload: dict = {
        "handoff_id": handoff_path.stem,
        "created_at": created_at,
        "from_agent": from_agent,
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
    return _relative(handoff_path, repo_root)


def apply_command(
    repo_root: Path,
    *,
    command: Literal["yes", "no", "revise", "switch"],
    target_agent: str | None = None,
    reason: str = "limit_reached",
    session_id: str | None = None,
    note: str | None = None,
    now: datetime | None = None,
    branch: str | None = None,
    head_sha: str | None = None,
    from_agent: str | None = None,
    auto_handoff: bool = True,
) -> CopilotCommandResult:
    """Apply a human copilot command as metadata-only evidence."""
    if command not in COMMANDS:
        raise ValueError(f"Unsupported copilot command: {command}")

    root = Path(repo_root)
    recommendation = recommend_next_step(root)
    timestamp_source = now or datetime.now(timezone.utc)
    timestamp = _handoff_timestamp(timestamp_source)
    created_at = _created_at(timestamp_source)

    if command == "yes":
        written_op = _write_operator_session(
            root,
            recommendation=recommendation,
            timestamp=timestamp,
            created_at=created_at,
            status="in_progress",
            notes=note or "Operator accepted the current recommendation.",
        )
        written_files: list[str] = [written_op]
        if auto_handoff and recommendation.recommended_next_agent != "human_operator":
            source_agent = from_agent or os.environ.get("CP_AGENT_NAME") or "human_operator"
            if source_agent not in ALLOWED_AGENTS:
                source_agent = "human_operator"
            if source_agent != recommendation.recommended_next_agent:
                resolved_branch = branch
                resolved_sha = head_sha
                if resolved_branch is None:
                    resolved_branch = _git_value(root, ["rev-parse", "--abbrev-ref", "HEAD"])
                if resolved_sha is None:
                    raw = _git_value(root, ["rev-parse", "HEAD"])
                    resolved_sha = raw[:12] if raw else None
                written_ho = _write_handoff_record(
                    root,
                    recommendation=recommendation,
                    target_agent=recommendation.recommended_next_agent,
                    reason=recommendation.recommended_reason,
                    timestamp=timestamp,
                    created_at=created_at,
                    from_agent=source_agent,
                    session_id=session_id,
                    branch=resolved_branch,
                    head_sha=resolved_sha,
                )
                written_files.append(written_ho)
        message = f"Operator session written: {written_op}"
        if len(written_files) > 1:
            message += f"; handoff written: {written_files[1]}"
        return CopilotCommandResult(
            written_files=tuple(written_files),
            next_recommendation=recommendation,
            message=message,
        )

    if command == "no":
        if not note or not note.strip():
            raise ValueError("no command requires note.")
        written = _write_operator_session(
            root,
            recommendation=recommendation,
            timestamp=timestamp,
            created_at=created_at,
            status="skipped",
            notes=note.strip(),
        )
        return CopilotCommandResult(
            written_files=(written,),
            next_recommendation=recommendation,
            message=f"Operator skip session written: {written}",
        )

    if command == "revise":
        if not note or not note.strip():
            raise ValueError("revise command requires note.")
        if recommendation.current_task in PROMPT_RELATED_TASKS:
            written = _write_prompt_revision_brief(
                root,
                recommendation=recommendation,
                note=note.strip(),
            )
            return CopilotCommandResult(
                written_files=(written,),
                next_recommendation=recommendation,
                message=f"Prompt revision brief written: {written}",
            )
        written = _write_revision_markdown(
            root,
            recommendation=recommendation,
            timestamp=timestamp,
            created_at=created_at,
            note=note.strip(),
        )
        return CopilotCommandResult(
            written_files=(written,),
            next_recommendation=recommendation,
            message=f"Operator revision note written: {written}",
        )

    # switch
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

    if branch is None:
        branch = _git_value(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if head_sha is None:
        raw_head_sha = _git_value(root, ["rev-parse", "HEAD"])
        head_sha = raw_head_sha[:12] if raw_head_sha else None

    written = _write_handoff_record(
        root,
        recommendation=recommendation,
        target_agent=target_agent,
        reason=reason,
        timestamp=timestamp,
        created_at=created_at,
        from_agent=source_agent,
        session_id=session_id,
        branch=branch,
        head_sha=head_sha,
    )
    return CopilotCommandResult(
        written_files=(written,),
        next_recommendation=recommendation,
        message=f"Handoff written. Paste this path to your next agent: {written}",
    )
