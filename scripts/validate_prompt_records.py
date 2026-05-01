import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def parse_args():
    parser = argparse.ArgumentParser(description="Validate prompt records against schema.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root directory"
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("evidence/validation_reports/prompt_records_validation_report.json"),
        help="Output JSON report path"
    )
    return parser.parse_args()


def main(args=None):
    if args is None:
        args = parse_args()

    repo_root = args.repo_root
    report_path = repo_root / args.report_json if not args.report_json.is_absolute() else args.report_json

    schema_path = repo_root / "schemas" / "prompt_record.schema.json"
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}")
        return 1

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)

    prompt_dirs = ["draft", "review", "approved", "locked"]
    yaml_files = []
    for d in prompt_dirs:
        dir_path = repo_root / "prompts" / d
        if dir_path.exists():
            yaml_files.extend(list(dir_path.glob("*.yaml")))

    report = {
        "total_files_scanned": len(yaml_files),
        "files_with_errors": 0,
        "errors": {}
    }

    if not yaml_files:
        print("0 files validated.")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return 0

    has_errors = False
    for file_path in yaml_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                instance = yaml.safe_load(f)

            errors = list(validator.iter_errors(instance))
            if errors:
                has_errors = True
                report["files_with_errors"] += 1
                report["errors"][str(file_path.relative_to(repo_root))] = [
                    f"{e.json_path}: {e.message}" for e in errors
                ]
        except Exception as e:
            has_errors = True
            report["files_with_errors"] += 1
            report["errors"][str(file_path.relative_to(repo_root))] = [f"File parsing error: {str(e)}"]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if has_errors:
        print(f"Validation failed. See {report_path} for details.")
        return 1

    print(f"{len(yaml_files)} files validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())