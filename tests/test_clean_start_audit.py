from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.clean_start_audit import (  # noqa: E402
    build_clean_start_audit,
    main as clean_start_audit_main,
    write_clean_start_audit,
)
from scripts.validate_production_records import run_validation  # noqa: E402


MEDIA_EXTENSIONS = {
    ".aiff",
    ".avi",
    ".flac",
    ".gif",
    ".jpeg",
    ".jpg",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".png",
    ".psd",
    ".tif",
    ".tiff",
    ".wav",
    ".webm",
    ".webp",
}


def _load_schema() -> dict:
    return json.loads(
        (REPO_ROOT / "schemas/clean_start_audit.schema.json").read_text(
            encoding="utf-8"
        )
    )


def _load_real_audit() -> dict:
    return yaml.safe_load(
        (
            REPO_ROOT
            / "evidence/clean_start_audits/SC0001_pre_asset_start.yaml"
        ).read_text(encoding="utf-8")
    )


def _git_tracked_paths() -> list[str]:
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_real_clean_start_audit_is_schema_valid() -> None:
    audit = _load_real_audit()
    schema = _load_schema()

    assert list(Draft202012Validator(schema).iter_errors(audit)) == []


def test_build_clean_start_audit_captures_pre_asset_baseline() -> None:
    audit = build_clean_start_audit(REPO_ROOT, "SC0001")

    assert audit["audit_status"] == "clean_pre_asset_baseline"
    assert audit["ready_for_first_asset_intake"] is True
    assert audit["blocked_for_kling_generation"] is True
    assert audit["summary"]["tracked_media_binaries_found"] is False
    assert audit["summary"]["canonical_assets_present"] is False
    assert audit["external_generation_performed"] is False
    assert audit["pack_locking_performed"] is False
    assert audit["lifecycle_promotion_performed"] is False


def test_publication_checkpoint_records_v030_zenodo_doi() -> None:
    audit = _load_real_audit()

    assert audit["publication_checkpoint"] == {
        "public_release_version": "v0.3.0",
        "zenodo_doi": "10.5281/zenodo.20036189",
        "zenodo_record": "https://zenodo.org/records/20036189",
        "citation_updated": True,
    }


def test_sc0001_gate_and_pack_baseline_remain_blocked_and_metadata_only() -> None:
    audit = _load_real_audit()

    assert audit["sc0001_gate_state"]["ready_for_kling_prompt_generation"] is False
    assert audit["sc0001_gate_state"]["gate_status"] == (
        "blocked_pending_locked_element_packs"
    )
    assert audit["sc0001_gate_state"]["ready_packs"] == 0
    assert audit["sc0001_gate_state"]["metadata_only_packs"] == 4
    assert audit["pack_baseline"]["required_pack_count"] == 4
    assert audit["pack_baseline"]["metadata_only_pack_count"] == 4
    assert audit["pack_baseline"]["ready_for_lock_review"] == 0
    assert audit["pack_baseline"]["packs_missing_canonical_assets"] == 4


def test_no_tracked_image_video_or_audio_binaries_before_first_asset() -> None:
    tracked_media = [
        path
        for path in _git_tracked_paths()
        if Path(path).suffix.lower() in MEDIA_EXTENSIONS
    ]

    assert tracked_media == []


def test_no_canonical_assets_are_committed_before_b8a() -> None:
    audit = _load_real_audit()

    assert audit["summary"]["canonical_assets_present"] is False
    assert audit["summary"]["canonical_asset_count"] == 0
    assert audit["canonical_assets_committed"] == []


def test_local_artifacts_are_separated_from_repo_baseline() -> None:
    audit = _load_real_audit()
    artifacts = {artifact["path"]: artifact for artifact in audit["local_non_baseline_artifacts"]}

    assert artifacts["evidence/provenance/dryrun-z1p1/"]["affects_repo_baseline"] is False
    assert artifacts[".claude/worktrees/"]["part_of_first_asset_intake"] is False
    assert artifacts["prompts/prompt_library.yaml"]["staged_for_this_batch"] is False
    assert artifacts["prompts/prompt_library.yaml"]["touched_by_this_batch"] is False


def test_cli_writes_schema_valid_clean_start_record(tmp_path: Path) -> None:
    output_path = tmp_path / "SC0001_pre_asset_start.yaml"

    code = clean_start_audit_main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--scene-id",
            "SC0001",
            "--output-path",
            str(output_path),
        ]
    )
    audit = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert code == 0
    assert audit["binary_outputs_created"] is False
    assert list(Draft202012Validator(_load_schema()).iter_errors(audit)) == []
    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.mp4"))


def test_write_clean_start_audit_has_no_binary_side_effects(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "SC0001_pre_asset_start.yaml"

    written_path = write_clean_start_audit(
        REPO_ROOT,
        "SC0001",
        output_path=output_path,
    )

    assert written_path == output_path
    assert output_path.exists()
    assert not list(tmp_path.rglob("*.jpg"))
    assert not list(tmp_path.rglob("*.mov"))


def test_production_validator_includes_clean_start_audit_records() -> None:
    report = run_validation(REPO_ROOT)

    assert report.by_record_type["clean_start_audit"] == 1
    assert report.invalid_files == 0
    assert report.has_errors is False
