"""
tests/test_prompt_record_validation.py — Batch 1

Tests for scripts/validate_prompt_records.py.
All tests use tmp_path — never write to real prompts/ directory.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_prompt_records import (
    collect_prompt_files,
    run_validation,
    PromptValidationReport,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_RECORD = {
    "prompt_id": "SC0001__t2i-char-nadia-midjourney__v01",
    "scene_id": "SC0001",
    "prompt_type": "t2i_character_element",
    "lifecycle_stage": "draft",
    "target_models": ["midjourney"],
    "source_refs": {
        "scene_card": "planning/scenes/SC0001/scene_card.yaml",
        "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
    },
    "prompt_text": "Pale young woman, hospital bracelet, corridor shadows --ar 16:9 --v 6.1",
    "status": "active",
    "canon_lock": False,
}


def write_prompt_file(prompts_dir: Path, subdir: str, filename: str, data: dict) -> Path:
    (prompts_dir / subdir).mkdir(parents=True, exist_ok=True)
    path = prompts_dir / subdir / filename
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# collect_prompt_files()
# ---------------------------------------------------------------------------


def test_collect_prompt_files_finds_yaml_in_subdirs(tmp_path):
    prompts_dir = tmp_path / "prompts"
    write_prompt_file(prompts_dir, "draft", "record1.yaml", MINIMAL_VALID_RECORD)
    write_prompt_file(prompts_dir, "approved", "record2.yaml", MINIMAL_VALID_RECORD)
    files = collect_prompt_files(prompts_dir)
    assert len(files) == 2


def test_collect_prompt_files_empty_dir(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    files = collect_prompt_files(prompts_dir)
    assert files == []


def test_collect_prompt_files_missing_dir(tmp_path):
    prompts_dir = tmp_path / "prompts"
    # Not created — should return empty list, not raise
    files = collect_prompt_files(prompts_dir)
    assert files == []


# ---------------------------------------------------------------------------
# run_validation() — valid record
# ---------------------------------------------------------------------------


def test_valid_minimal_record_passes(tmp_path):
    prompts_dir = tmp_path / "prompts"
    write_prompt_file(prompts_dir, "draft", "valid.yaml", MINIMAL_VALID_RECORD)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.total_files == 1
    assert report.valid_files == 1
    assert report.invalid_files == 0
    assert report.issues == []
    assert not report.has_errors


# ---------------------------------------------------------------------------
# run_validation() — invalid records
# ---------------------------------------------------------------------------


def test_missing_prompt_text_fails(tmp_path):
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD}
    del bad["prompt_text"]
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.has_errors
    assert any("prompt_text" in i.message or "prompt_text" in i.field_path
               for i in report.issues)


def test_invalid_prompt_id_pattern_fails(tmp_path):
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD, "prompt_id": "INVALID_ID"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.has_errors
    assert any("prompt_id" in i.field_path for i in report.issues)


def test_invalid_prompt_type_enum_fails(tmp_path):
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD, "prompt_type": "invalid_type_xyz"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.has_errors
    assert any("prompt_type" in i.field_path for i in report.issues)


def test_invalid_lifecycle_stage_fails(tmp_path):
    """lifecycle_stage='production' is not in the schema enum — must fail."""
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD, "lifecycle_stage": "production"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.has_errors
    assert any("lifecycle_stage" in i.field_path for i in report.issues)


# ---------------------------------------------------------------------------
# run_validation() — empty directory
# ---------------------------------------------------------------------------


def test_empty_prompts_dir_exits_zero(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.total_files == 0
    assert report.valid_files == 0
    assert report.invalid_files == 0
    assert not report.has_errors


def test_nonexistent_prompts_dir_exits_zero(tmp_path):
    prompts_dir = tmp_path / "prompts_nonexistent"
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.total_files == 0
    assert not report.has_errors


# ---------------------------------------------------------------------------
# run_validation() — JSON report output
# ---------------------------------------------------------------------------


def test_report_json_written(tmp_path):
    prompts_dir = tmp_path / "prompts"
    write_prompt_file(prompts_dir, "draft", "valid.yaml", MINIMAL_VALID_RECORD)
    report_path = tmp_path / "reports" / "report.json"
    run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir, report_json=report_path)
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["total_files"] == 1
    assert data["valid_files"] == 1
    assert data["issues"] == []


def test_report_json_records_errors(tmp_path):
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD, "prompt_id": "BAD"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report_path = tmp_path / "reports" / "report.json"
    run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir, report_json=report_path)
    data = json.loads(report_path.read_text())
    assert data["invalid_files"] == 1
    assert len(data["issues"]) >= 1


# ---------------------------------------------------------------------------
# Multiple files
# ---------------------------------------------------------------------------


def test_multiple_files_one_invalid(tmp_path):
    prompts_dir = tmp_path / "prompts"
    write_prompt_file(prompts_dir, "draft", "valid.yaml", MINIMAL_VALID_RECORD)
    bad = {**MINIMAL_VALID_RECORD, "prompt_type": "not_valid"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    report = run_validation(repo_root=REPO_ROOT, prompts_dir=prompts_dir)
    assert report.total_files == 2
    assert report.valid_files == 1
    assert report.invalid_files == 1
    assert report.has_errors


# ---------------------------------------------------------------------------
# CLI (via subprocess to match CI contract)
# ---------------------------------------------------------------------------


def test_cli_exit_0_on_empty_prompts(tmp_path):
    import subprocess
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_prompt_records.py"),
            "--repo-root", str(REPO_ROOT),
            "--prompts-dir", str(prompts_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0 files validated" in result.stdout


def test_cli_exit_1_on_invalid_record(tmp_path):
    import subprocess
    prompts_dir = tmp_path / "prompts"
    bad = {**MINIMAL_VALID_RECORD, "prompt_id": "BAD_ID_FORMAT"}
    write_prompt_file(prompts_dir, "draft", "bad.yaml", bad)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_prompt_records.py"),
            "--repo-root", str(REPO_ROOT),
            "--prompts-dir", str(prompts_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
