"""
validate_prompt_records.py — Batch 1

Validates all prompt YAML files in prompts/{draft,review,approved,locked}/
against schemas/prompt_record.schema.json using Draft202012Validator.

Usage:
    python scripts/validate_prompt_records.py --repo-root .
    python scripts/validate_prompt_records.py --repo-root . --prompts-dir prompts
    python scripts/validate_prompt_records.py --repo-root . --report-json evidence/validation_reports/prompt_records_validation_report.json

Exit codes:
    0 — all files pass (or no files found)
    1 — one or more files fail schema validation

CI contract:
    - Empty prompts/ directory exits 0 with message "0 files validated"
    - Never fails on missing subdirectories (draft/review/approved/locked may not all exist)
    - Writes JSON report to evidence/validation_reports/ if --report-json specified
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


# Prompt lifecycle subdirectories to scan (in validation order)
PROMPT_SUBDIRS = ["draft", "review", "approved", "locked"]


@dataclass
class PromptValidationIssue:
    file: str
    field_path: str
    message: str


@dataclass
class PromptValidationReport:
    total_files: int
    valid_files: int
    invalid_files: int
    issues: list[PromptValidationIssue]

    @property
    def has_errors(self) -> bool:
        return self.invalid_files > 0


def load_schema(schema_path: Path) -> dict[str, Any]:
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_prompt_files(prompts_dir: Path) -> list[Path]:
    """Return all *.yaml files under prompts/{draft,review,approved,locked}/."""
    files: list[Path] = []
    for subdir in PROMPT_SUBDIRS:
        subdir_path = prompts_dir / subdir
        if subdir_path.is_dir():
            files.extend(sorted(subdir_path.glob("*.yaml")))
    return files


def validate_prompt_file(
    path: Path,
    validator: Draft202012Validator,
) -> list[PromptValidationIssue]:
    """Validate a single prompt YAML file. Returns list of issues (empty = valid)."""
    issues: list[PromptValidationIssue] = []

    try:
        data = load_yaml_file(path)
    except Exception as exc:
        issues.append(
            PromptValidationIssue(
                file=str(path),
                field_path="",
                message=f"YAML parse error: {exc}",
            )
        )
        return issues

    if data is None:
        issues.append(
            PromptValidationIssue(
                file=str(path),
                field_path="",
                message="File is empty or contains only comments.",
            )
        )
        return issues

    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for error in errors:
        field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        issues.append(
            PromptValidationIssue(
                file=str(path),
                field_path=field_path,
                message=error.message,
            )
        )

    return issues


def run_validation(
    repo_root: Path,
    prompts_dir: Path | None = None,
    report_json: Path | None = None,
) -> PromptValidationReport:
    """
    Run prompt record validation.

    Args:
        repo_root: Absolute path to the repository root.
        prompts_dir: Directory to scan (default: repo_root/prompts).
        report_json: Optional path to write JSON report.

    Returns:
        PromptValidationReport with results.
    """
    prompts_dir = prompts_dir or (repo_root / "prompts")
    schema_path = repo_root / "schemas" / "prompt_record.schema.json"

    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)

    prompt_files = collect_prompt_files(prompts_dir)

    total = len(prompt_files)
    all_issues: list[PromptValidationIssue] = []
    invalid_count = 0

    for path in prompt_files:
        file_issues = validate_prompt_file(path, validator)
        if file_issues:
            invalid_count += 1
            all_issues.extend(file_issues)

    report = PromptValidationReport(
        total_files=total,
        valid_files=total - invalid_count,
        invalid_files=invalid_count,
        issues=all_issues,
    )

    if report_json is not None:
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "total_files": report.total_files,
            "valid_files": report.valid_files,
            "invalid_files": report.invalid_files,
            "issues": [asdict(i) for i in report.issues],
        }
        with report_json.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    return report


def print_report(report: PromptValidationReport) -> None:
    """Print validation summary to stdout."""
    if report.total_files == 0:
        print("0 files validated — prompts/ contains no YAML files.")
        return

    print(f"Prompt record validation: {report.total_files} files scanned.")
    print(f"  Valid:   {report.valid_files}")
    print(f"  Invalid: {report.invalid_files}")

    if report.issues:
        print()
        print("Validation errors:")
        for issue in report.issues:
            print(f"  [{issue.file}] {issue.field_path}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate prompt record YAML files against prompt_record.schema.json."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory).",
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=None,
        help="Prompts directory to scan (default: <repo-root>/prompts).",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Path to write JSON validation report (optional).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    prompts_dir = args.prompts_dir.resolve() if args.prompts_dir else None
    report_json = args.report_json.resolve() if args.report_json else None

    report = run_validation(repo_root=repo_root, prompts_dir=prompts_dir, report_json=report_json)
    print_report(report)

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
