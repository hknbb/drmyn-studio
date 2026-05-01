"""
Print-only pull request suggestion helper.

Composes a suggested GitHub CLI command and body text from the current branch,
changed files, and the latest operator session. It never executes ``gh`` and
does not write a pull request body file.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml


PROTECTED_BRANCHES = {"main", "master"}


@dataclass(frozen=True)
class PrSuggestion:
    branch: str
    title: str
    body_lines: tuple[str, ...]
    gh_command_str: str
    changed_files: tuple[str, ...]


def _git_output(repo_root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ValueError(f"git command failed to start: git {' '.join(args)}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"git command failed: git {' '.join(args)}: {detail}")
    return result.stdout.strip()


def _branch_from_git(repo_root: Path) -> str:
    branch = _git_output(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "HEAD":
        raise ValueError("Cannot suggest a PR from detached HEAD.")
    return branch


def _changed_files(repo_root: Path, base: str) -> tuple[str, ...]:
    output = _git_output(repo_root, ["diff", "--name-only", f"{base}...HEAD"])
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _title_from_branch(branch: str) -> str:
    slug = branch
    if slug.startswith("feat/batch-"):
        slug = slug.removeprefix("feat/batch-")
    else:
        slug = slug.replace("/", "-")
    label = re.sub(r"[-_]+", " ", slug).strip()
    return f"[codex] {label}" if label else "[codex] production update"


def _quote_cli_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _latest_operator_session(repo_root: Path) -> dict | None:
    sessions_dir = repo_root / "evidence" / "operator_sessions"
    candidates = sorted(sessions_dir.glob("OP-*.yaml"))
    for path in reversed(candidates):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    return None


def _body_lines(
    *,
    branch: str,
    changed_files: tuple[str, ...],
    operator_session: dict | None,
) -> tuple[str, ...]:
    current_task = (
        str(operator_session.get("current_task"))
        if operator_session and operator_session.get("current_task")
        else "No operator session found."
    )
    recommended_steps = (
        operator_session.get("recommended_steps", []) if operator_session else []
    )
    if not isinstance(recommended_steps, list):
        recommended_steps = []

    lines = [
        "## Summary",
        f"- Branch: `{branch}`",
        f"- Current task: {current_task}",
        "",
        "## Recommended Steps",
    ]
    if recommended_steps:
        lines.extend(f"- {step}" for step in recommended_steps)
    else:
        lines.append("- No operator session recommendations found.")

    lines.extend(["", "## Changed Files"])
    if changed_files:
        lines.extend(f"- `{path}`" for path in changed_files)
    else:
        lines.append("- No changed files detected against base.")

    lines.extend(
        [
            "",
            "## Safety",
            "- No binary commits.",
            "- No lifecycle promotion.",
        ]
    )
    return tuple(lines)


def suggest_pr(
    repo_root: Path,
    *,
    branch: str | None = None,
    base: str = "main",
) -> PrSuggestion:
    """Compose a gh pr create suggestion. Print-only, no execution."""
    root = Path(repo_root)
    selected_branch = branch or _branch_from_git(root)
    if selected_branch in PROTECTED_BRANCHES:
        raise ValueError("Refusing to suggest a PR from main/master.")

    changed_files = _changed_files(root, base)
    title = _title_from_branch(selected_branch)
    session = _latest_operator_session(root)
    body_lines = _body_lines(
        branch=selected_branch,
        changed_files=changed_files,
        operator_session=session,
    )
    gh_command = " ".join(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base,
            "--head",
            selected_branch,
            "--title",
            _quote_cli_value(title),
            "--body-file",
            "<body-file-path>",
        ]
    )

    return PrSuggestion(
        branch=selected_branch,
        title=title,
        body_lines=body_lines,
        gh_command_str=gh_command,
        changed_files=changed_files,
    )
