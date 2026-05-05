"""Testable command helpers for the copilot dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from scripts.agents.copilot_command import apply_command


CopilotCommand = Literal["yes", "no", "revise", "switch"]

COMMANDS: tuple[CopilotCommand, ...] = ("yes", "no", "revise", "switch")
TARGET_AGENT_OPTIONS = (
    "claude_code",
    "codex",
    "gemini_code_assist",
)
HANDOFF_REASON_OPTIONS = (
    "manual_pickup",
    "limit_reached",
    "review_requested",
    "second_opinion",
    "drafting_assist",
    "context_too_large",
    "task_complete",
)


class ApplyCommandFn(Protocol):
    def __call__(
        self,
        repo_root: Path,
        *,
        command: CopilotCommand,
        target_agent: str | None = None,
        reason: str = "manual_pickup",
        session_id: str | None = None,
        note: str | None = None,
    ) -> object:
        ...


@dataclass(frozen=True)
class CommandUiResult:
    applied: bool
    message: str
    written_files: tuple[str, ...] = ()


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_allowed(allowed_commands: object) -> set[str] | None:
    if allowed_commands is None:
        return None
    if not isinstance(allowed_commands, (list, tuple, set)):
        return set()
    return {str(command) for command in allowed_commands}


def validate_command_inputs(
    *,
    command: str,
    note: str | None = None,
    target_agent: str | None = None,
    allowed_commands: object = None,
) -> str | None:
    """Return a validation error, or None when the command may be applied."""
    if command not in COMMANDS:
        return f"Unsupported copilot command: {command}"

    allowed = _normalize_allowed(allowed_commands)
    if allowed is not None and command not in allowed:
        return f"Command is not allowed by the current recommendation: {command}"

    if command in {"no", "revise"} and _clean_text(note) is None:
        return f"{command} requires a note."

    if command == "switch" and _clean_text(target_agent) is None:
        return "switch requires target_agent."

    return None


def run_dashboard_command(
    repo_root: str | Path,
    *,
    command: CopilotCommand,
    note: str | None = None,
    target_agent: str | None = None,
    reason: str = "manual_pickup",
    session_id: str | None = None,
    allowed_commands: object = None,
    apply_fn: ApplyCommandFn = apply_command,
) -> CommandUiResult:
    """Validate and apply one dashboard command through the canonical writer."""
    cleaned_note = _clean_text(note)
    cleaned_target_agent = _clean_text(target_agent)
    error = validate_command_inputs(
        command=command,
        note=cleaned_note,
        target_agent=cleaned_target_agent,
        allowed_commands=allowed_commands,
    )
    if error is not None:
        return CommandUiResult(applied=False, message=error)

    try:
        result = apply_fn(
            Path(repo_root),
            command=command,
            target_agent=cleaned_target_agent,
            reason=reason,
            session_id=session_id,
            note=cleaned_note,
        )
    except ValueError as exc:
        return CommandUiResult(applied=False, message=str(exc))

    written_files = tuple(str(path) for path in getattr(result, "written_files", ()))
    message = str(getattr(result, "message", "Command applied."))
    return CommandUiResult(
        applied=True,
        message=message,
        written_files=written_files,
    )
