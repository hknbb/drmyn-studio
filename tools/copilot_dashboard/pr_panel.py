"""Suggestion-only PR helper panel data for the copilot dashboard."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.pr_helper import suggest_pr


class SuggestPrFn(Protocol):
    def __call__(
        self,
        repo_root: Path,
        *,
        branch: str | None = None,
        base: str = "main",
    ) -> object:
        ...


@dataclass(frozen=True)
class PrPanelData:
    available: bool
    message: str
    branch: str = ""
    title: str = ""
    changed_files: tuple[str, ...] = ()
    body_preview: str = ""
    gh_command_str: str = ""


def load_pr_panel_data(
    repo_root: str | Path,
    *,
    branch: str | None = None,
    base: str = "main",
    suggest_fn: SuggestPrFn = suggest_pr,
) -> PrPanelData:
    """Load print-only PR suggestion data without creating or updating a PR."""
    try:
        suggestion = suggest_fn(Path(repo_root), branch=branch, base=base)
    except ValueError as exc:
        return PrPanelData(available=False, message=str(exc))

    body_lines = tuple(str(line) for line in getattr(suggestion, "body_lines", ()))
    changed_files = tuple(str(path) for path in getattr(suggestion, "changed_files", ()))
    return PrPanelData(
        available=True,
        message="PR suggestion ready. Human operator must run or edit it manually.",
        branch=str(getattr(suggestion, "branch", "")),
        title=str(getattr(suggestion, "title", "")),
        changed_files=changed_files,
        body_preview="\n".join(body_lines),
        gh_command_str=str(getattr(suggestion, "gh_command_str", "")),
    )
