from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.pr_helper import suggest_pr  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _git_result(stdout: str) -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def test_suggest_pr_composes_print_only_command_and_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(args: list[str], **kwargs: object) -> SimpleNamespace:
        del kwargs
        calls.append(tuple(args))
        if args == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return _git_result("feat/batch-ha-3c-pr-helper\n")
        if args == ["git", "diff", "--name-only", "main...HEAD"]:
            return _git_result(
                "scripts/agents/pr_helper.py\n"
                "scripts/agents/run_pipeline.py\n"
                "tests/test_pr_helper.py\n"
            )
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr("scripts.agents.pr_helper.subprocess.run", fake_run)
    _write_yaml(
        tmp_path / "evidence/operator_sessions/OP-20260501-120000.yaml",
        {
            "session_id": "OP-20260501-120000",
            "created_at": "2026-05-01T12:00:00Z",
            "scene_id": None,
            "current_task": "pr_helper_print_only",
            "recommended_files": ["scripts/agents/pr_helper.py"],
            "recommended_steps": [
                "Review the helper output.",
                "Run gh manually only after human approval.",
            ],
            "status": "in_progress",
            "notes": "",
        },
    )

    suggestion = suggest_pr(tmp_path)

    assert calls == [
        ("git", "rev-parse", "--abbrev-ref", "HEAD"),
        ("git", "diff", "--name-only", "main...HEAD"),
    ]
    assert suggestion.branch == "feat/batch-ha-3c-pr-helper"
    assert suggestion.title == "[codex] ha 3c pr helper"
    assert suggestion.changed_files == (
        "scripts/agents/pr_helper.py",
        "scripts/agents/run_pipeline.py",
        "tests/test_pr_helper.py",
    )
    assert suggestion.gh_command_str == (
        'gh pr create --base main --head feat/batch-ha-3c-pr-helper '
        '--title "[codex] ha 3c pr helper" --body-file <body-file-path>'
    )
    assert "## Summary" in suggestion.body_lines
    assert "- Current task: pr_helper_print_only" in suggestion.body_lines
    assert "- No binary commits." in suggestion.body_lines
    assert "- No lifecycle promotion." in suggestion.body_lines
    assert not (tmp_path / "<body-file-path>").exists()


def test_suggest_pr_rejects_main_without_git_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(args: list[str], **kwargs: object) -> SimpleNamespace:
        del kwargs
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr("scripts.agents.pr_helper.subprocess.run", fake_run)

    with pytest.raises(ValueError, match="main/master"):
        suggest_pr(tmp_path, branch="main")


def test_suggest_pr_uses_fallback_body_without_operator_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(args: list[str], **kwargs: object) -> SimpleNamespace:
        del kwargs
        if args == ["git", "diff", "--name-only", "main...HEAD"]:
            return _git_result("")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr("scripts.agents.pr_helper.subprocess.run", fake_run)

    suggestion = suggest_pr(tmp_path, branch="feat/example")

    assert suggestion.title == "[codex] feat example"
    assert suggestion.changed_files == ()
    assert "- Current task: No operator session found." in suggestion.body_lines
    assert "- No operator session recommendations found." in suggestion.body_lines
    assert "- No changed files detected against base." in suggestion.body_lines
