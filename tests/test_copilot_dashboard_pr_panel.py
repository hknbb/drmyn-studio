from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.copilot_dashboard import pr_panel  # noqa: E402


def test_pr_panel_helper_calls_suggest_pr_and_returns_display_data(tmp_path: Path) -> None:
    calls: list[tuple[Path, dict[str, object]]] = []

    def fake_suggest_pr(repo_root: Path, **kwargs: object) -> SimpleNamespace:
        calls.append((repo_root, kwargs))
        return SimpleNamespace(
            branch="feat/example",
            title="[codex] example",
            changed_files=("tools/copilot_dashboard/app.py",),
            body_lines=("## Summary", "- Example PR body."),
            gh_command_str=(
                'gh pr create --base main --head feat/example '
                '--title "[codex] example" --body-file <body-file-path>'
            ),
        )

    data = pr_panel.load_pr_panel_data(tmp_path, suggest_fn=fake_suggest_pr)

    assert calls == [(tmp_path, {"branch": None, "base": "main"})]
    assert data.available is True
    assert data.branch == "feat/example"
    assert data.title == "[codex] example"
    assert data.changed_files == ("tools/copilot_dashboard/app.py",)
    assert data.body_preview == "## Summary\n- Example PR body."
    assert data.gh_command_str.startswith("gh pr create")
    assert not (tmp_path / "<body-file-path>").exists()


def test_pr_panel_main_branch_error_is_display_data(tmp_path: Path) -> None:
    def fake_suggest_pr(repo_root: Path, **kwargs: object) -> object:
        del repo_root, kwargs
        raise ValueError("Refusing to suggest a PR from main/master.")

    data = pr_panel.load_pr_panel_data(
        tmp_path,
        branch="main",
        suggest_fn=fake_suggest_pr,
    )

    assert data.available is False
    assert data.message == "Refusing to suggest a PR from main/master."
    assert data.gh_command_str == ""
    assert not list(tmp_path.rglob("*"))


def test_pr_panel_does_not_execute_gh_or_write_files(tmp_path: Path) -> None:
    def fake_suggest_pr(repo_root: Path, **kwargs: object) -> SimpleNamespace:
        del repo_root, kwargs
        return SimpleNamespace(
            branch="feat/no-exec",
            title="[codex] no exec",
            changed_files=(),
            body_lines=("## Summary", "- No execution."),
            gh_command_str="gh pr create --base main --head feat/no-exec",
        )

    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    data = pr_panel.load_pr_panel_data(tmp_path, suggest_fn=fake_suggest_pr)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert data.available is True
    assert data.gh_command_str == "gh pr create --base main --head feat/no-exec"
    assert after == before
