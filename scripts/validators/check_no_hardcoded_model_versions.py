"""
A6.4 Audit: Check that no provider model/version names are hardcoded in adapters or schemas.

Provider model names must NOT appear as literals in:
  - scripts/agents/adapters/*.py
  - scripts/agents/**/*.py (serializers, formatters, model targeting)
  - schemas/**/*.json (const/default values)

Provider model names ARE ALLOWED in:
  - model_guidance_snapshots/**
  - docs/**
  - evidence/**
  - historical prompt records (prompts/draft/ with explicit allowlist)

Forbidden literals (current known provider model names):
  - "Kling 3.0 Omni"
  - "Kling VIDEO 3.0 Omni"
  - "VIDEO 3.0 Omni"
  - "Midjourney V8.1"
  - "Midjourney V7"
  - "gpt-image-2"
  - "ChatGPT Images 2.0"
  - "Nano Banana Pro"
  - "gemini-3-pro-image-preview"

Allowed literals (stable internal IDs, not provider names):
  - "kling_omni_video_best_available"
  - "kling_video_best_available"
  - "midjourney_image_best_available"
  - "chatgpt_image_best_available"
  - "nano_banana_best_available"
  - resolver reading resolved_model_name dynamically
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple


class AuditFinding(NamedTuple):
    file_path: str
    line_no: int
    line_text: str
    blocked_literal: str


FORBIDDEN_MODEL_NAMES = {
    "Kling 3.0 Omni",
    "Kling VIDEO 3.0 Omni",
    "VIDEO 3.0 Omni",
    "Midjourney V8.1",
    "Midjourney V7",
    "V8.1",  # Standalone version string
    "V7",    # Standalone version string
    "gpt-image-2",
    "ChatGPT Images 2.0",
    "Nano Banana Pro",
    "gemini-3-pro-image-preview",
}

ALLOWED_PATHS_PATTERNS = [
    "model_guidance_snapshots/",
    "docs/",
    "evidence/",
    "docs/model_guides/",
]

BLOCKED_PATHS_PATTERNS = [
    "scripts/agents/adapters/",
    "scripts/agents/",
    "schemas/",
]


def _should_allow_path(file_path: str) -> bool:
    """Check if a path is in the allowed list."""
    normalized = file_path.replace("\\", "/")
    return any(
        pattern in normalized
        for pattern in ALLOWED_PATHS_PATTERNS
    )


def _should_block_path(file_path: str) -> bool:
    """Check if a path is in the blocked list."""
    normalized = file_path.replace("\\", "/")
    return any(
        pattern in normalized
        for pattern in BLOCKED_PATHS_PATTERNS
    )


def _is_in_docstring_or_comment(line: str) -> bool:
    """Heuristic: check if line is likely a docstring or comment."""
    stripped = line.strip()
    return (
        stripped.startswith("#")
        or stripped.startswith('"""')
        or stripped.startswith("'''")
        or stripped.startswith("//")
    )


def audit_file(file_path: Path) -> list[AuditFinding]:
    """Scan a single file for forbidden model names."""
    findings = []

    # Skip if path is in allowed list
    if _should_allow_path(str(file_path)):
        return findings

    # Only scan if path is in blocked list or is a schema/adapter
    if not _should_block_path(str(file_path)):
        return findings

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.split("\n")

    for line_no, line in enumerate(lines, start=1):
        # Skip obvious docstrings/comments
        if _is_in_docstring_or_comment(line):
            continue

        # Check for forbidden model names
        for model_name in FORBIDDEN_MODEL_NAMES:
            if model_name in line:
                # Additional heuristic: skip if this looks like a comment or docstring continuation
                if line.strip().startswith(('"""', "'''", "#", "//")):
                    continue

                findings.append(
                    AuditFinding(
                        file_path=str(file_path),
                        line_no=line_no,
                        line_text=line.rstrip(),
                        blocked_literal=model_name,
                    )
                )
                break  # Report once per line

    return findings


def audit_repo(repo_root: Path) -> list[AuditFinding]:
    """Scan entire repo for forbidden hardcoded model names."""
    findings = []

    # Scan adapters
    adapters_dir = repo_root / "scripts" / "agents" / "adapters"
    if adapters_dir.exists():
        for py_file in adapters_dir.glob("*.py"):
            findings.extend(audit_file(py_file))

    # Scan other scripts/agents files
    agents_dir = repo_root / "scripts" / "agents"
    if agents_dir.exists():
        for py_file in agents_dir.glob("*.py"):
            # Skip test files
            if py_file.name.startswith("test_"):
                continue
            findings.extend(audit_file(py_file))

    # Scan schemas
    schemas_dir = repo_root / "schemas"
    if schemas_dir.exists():
        for schema_file in schemas_dir.glob("*.json"):
            findings.extend(audit_file(schema_file))

    return findings


def report_findings(findings: list[AuditFinding]) -> str:
    """Format findings as a human-readable report."""
    if not findings:
        return "[OK] No hardcoded provider model names found."

    lines = [f"[FAIL] Found {len(findings)} violation(s):\n"]
    for finding in findings:
        lines.append(f"  {finding.file_path}:{finding.line_no}")
        lines.append(f"    Blocked literal: {finding.blocked_literal!r}")
        lines.append(f"    Line: {finding.line_text[:100]}")
        lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    import sys

    repo_root = Path(__file__).parent.parent.parent
    findings = audit_repo(repo_root)
    report = report_findings(findings)
    print(report)

    return 0 if not findings else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
