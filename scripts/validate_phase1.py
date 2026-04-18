from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


SCENE_ID_RE = re.compile(r"^SC\d{4}$")
CHAR_ID_RE = re.compile(r"^C\d{2}$")
LOC_ID_RE = re.compile(r"^LOC\d{3}$")


@dataclass
class ValidationIssue:
    level: str
    file: str
    message: str


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_scene_cards(planning_dir: Path, schema_path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)

    scene_dirs = sorted((planning_dir / "scenes").glob("SC*/scene_card.yaml"))
    if not scene_dirs:
        issues.append(
            ValidationIssue(
                level="error",
                file=str(planning_dir / "scenes"),
                message="No scene_card.yaml files found under planning/scenes/.",
            )
        )
        return issues

    seen_scene_ids: set[str] = set()

    for card_path in scene_dirs:
        data = load_yaml(card_path)

        for error in validator.iter_errors(data):
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Schema validation error: {error.message}",
                )
            )

        scene_id = data.get("scene_id")
        if not scene_id or not SCENE_ID_RE.match(scene_id):
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(card_path),
                    message="scene_id missing or malformed.",
                )
            )
        elif scene_id in seen_scene_ids:
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Duplicate scene_id detected: {scene_id}",
                )
            )
        else:
            seen_scene_ids.add(scene_id)

        scene_dir_name = card_path.parent.name
        if scene_id and scene_dir_name != scene_id:
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(card_path),
                    message=f"scene_id ({scene_id}) does not match parent directory ({scene_dir_name}).",
                )
            )

        for ref_name in ["screen_excerpt_ref", "prompt_brief_ref", "review_notes_ref"]:
            ref = data.get(ref_name)
            if ref and not (card_path.parent / ref).exists():
                issues.append(
                    ValidationIssue(
                        level="warning",
                        file=str(card_path),
                        message=f"Referenced companion file not found: {ref}",
                    )
                )

    return issues


def validate_source(source_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required = [
        "story_blueprint.md",
        "character_dossier.md",
        "project_config.json",
    ]
    for name in required:
        if not (source_dir / name).exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(source_dir / name),
                    message="Required canonical source file is missing.",
                )
            )
    return issues


def validate_prompt_library(prompts_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_dirs = ["draft", "review", "approved", "locked"]
    for name in required_dirs:
        p = prompts_dir / name
        if not p.exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    file=str(p),
                    message="Required prompt lifecycle directory is missing.",
                )
            )

    prompt_library = prompts_dir / "prompt_library.yaml"
    if not prompt_library.exists():
        issues.append(
            ValidationIssue(
                level="warning",
                file=str(prompt_library),
                message="prompt_library.yaml not found.",
            )
        )

    return issues


def write_json_report(path: Path, issues: list[ValidationIssue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": not any(i.level == "error" for i in issues),
        "issue_count": len(issues),
        "issues": [asdict(i) for i in issues],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md_report(path: Path, issues: list[ValidationIssue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 1 Validation Report",
        "",
        f"Total issues: {len(issues)}",
        "",
    ]
    if not issues:
        lines.append("No issues found.")
    else:
        for issue in issues:
            lines.append(f"- **{issue.level.upper()}** `{issue.file}` — {issue.message}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--planning-dir", required=True)
    parser.add_argument("--prompts-dir", required=True)
    parser.add_argument("--schemas-dir", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-md", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    planning_dir = Path(args.planning_dir)
    prompts_dir = Path(args.prompts_dir)
    schemas_dir = Path(args.schemas_dir)

    issues: list[ValidationIssue] = []
    issues.extend(validate_source(source_dir))
    issues.extend(validate_prompt_library(prompts_dir))
    issues.extend(
        validate_scene_cards(
            planning_dir=planning_dir,
            schema_path=schemas_dir / "scene_card.schema.json",
        )
    )

    write_json_report(Path(args.report_json), issues)
    write_md_report(Path(args.report_md), issues)

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    print(f"Validation complete: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
