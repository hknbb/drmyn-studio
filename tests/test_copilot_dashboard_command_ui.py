from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.copilot_dashboard import command_ui  # noqa: E402


@dataclass(frozen=True)
class FakeApplyResult:
    written_files: tuple[str, ...]
    message: str


class ApplyRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, dict]] = []

    def __call__(self, repo_root: Path, **kwargs: object) -> FakeApplyResult:
        self.calls.append((repo_root, kwargs))
        return FakeApplyResult(
            written_files=("evidence/operator_sessions/OP-20260502-120000.yaml",),
            message="operator session written",
        )


def test_yes_payload_calls_apply_command(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="yes",
        allowed_commands=("yes",),
        apply_fn=recorder,
    )

    assert result.applied is True
    assert result.written_files == (
        "evidence/operator_sessions/OP-20260502-120000.yaml",
    )
    assert recorder.calls == [
        (
            tmp_path,
            {
                "command": "yes",
                "target_agent": None,
                "reason": "manual_pickup",
                "session_id": None,
                "note": None,
            },
        )
    ]


def test_no_requires_note_and_produces_no_write(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="no",
        note="  ",
        allowed_commands=("no",),
        apply_fn=recorder,
    )

    assert result.applied is False
    assert result.written_files == ()
    assert result.message == "no requires a note."
    assert recorder.calls == []
    assert not list(tmp_path.rglob("*"))


def test_revise_requires_note_and_produces_no_write(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="revise",
        note=None,
        allowed_commands=("revise",),
        apply_fn=recorder,
    )

    assert result.applied is False
    assert result.written_files == ()
    assert result.message == "revise requires a note."
    assert recorder.calls == []
    assert not list(tmp_path.rglob("*"))


def test_switch_requires_target_agent_and_produces_no_write(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="switch",
        target_agent=" ",
        allowed_commands=("switch",),
        apply_fn=recorder,
    )

    assert result.applied is False
    assert result.written_files == ()
    assert result.message == "switch requires target_agent."
    assert recorder.calls == []
    assert not list(tmp_path.rglob("*"))


def test_switch_payload_calls_apply_command_with_target_and_reason(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="switch",
        target_agent="codex",
        reason="second_opinion",
        allowed_commands=("switch",),
        apply_fn=recorder,
    )

    assert result.applied is True
    assert recorder.calls == [
        (
            tmp_path,
            {
                "command": "switch",
                "target_agent": "codex",
                "reason": "second_opinion",
                "session_id": None,
                "note": None,
            },
        )
    ]


def test_disallowed_command_produces_no_write(tmp_path: Path) -> None:
    recorder = ApplyRecorder()

    result = command_ui.run_dashboard_command(
        tmp_path,
        command="yes",
        allowed_commands=("switch",),
        apply_fn=recorder,
    )

    assert result.applied is False
    assert result.written_files == ()
    assert result.message == "Command is not allowed by the current recommendation: yes"
    assert recorder.calls == []
    assert not list(tmp_path.rglob("*.mp4"))
    assert not list(tmp_path.rglob("*.mov"))
    assert not list(tmp_path.rglob("*.png"))
