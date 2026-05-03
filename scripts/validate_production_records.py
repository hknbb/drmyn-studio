"""
validate_production_records.py

Validates non-prompt production metadata records introduced from Batch 5.5
onward, including image selection, asset clearance, storyboard options, shot
list suggestions, batch jobs, operator sessions, video takes, and video review
evidence. This validator is metadata-only: it reads YAML records and never
mutates pack manifests, lifecycle state, image binaries, video files, or
prompts.

Usage:
    python scripts/validate_production_records.py --repo-root .
    python scripts/validate_production_records.py --repo-root . --report-json evidence/validation_reports/production_records_validation_report.json

Exit codes:
    0 - all files pass (or no files found)
    1 - one or more files fail validation

CI contract:
    - Empty production metadata paths exit 0 with message "0 files validated"
    - Missing optional directories do not fail validation
    - Writes JSON report to evidence/validation_reports/ if --report-json specified
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


IMAGE_SELECTION_PATTERN = "visual_dev/elements/**/image_selection.yaml"
PACK_SUGGESTION_PATTERN = "visual_dev/elements/**/pack_manifest_update_suggestion.yaml"
ASSET_CLEARANCE_PATTERN = "evidence/asset_clearance/*.yaml"
PROMPT_REVIEW_BRIEF_PATTERN = "evidence/prompt_reviews/*_brief.yaml"
STORYBOARD_OPTIONS_PATTERN = "visual_dev/storyboards/SC*/storyboard_options.yaml"
SHOT_LIST_OMNI_SUGGESTION_PATTERN = (
    "visual_dev/storyboards/SC*/shot_list_omni_suggestion.yaml"
)
BATCH_JOB_PATTERN = "evidence/batch_jobs/*.yaml"
OPERATOR_SESSION_PATTERN = "evidence/operator_sessions/*.yaml"
AGENT_HANDOFF_PATTERN = "evidence/agent_handoffs/*.yaml"
LOCAL_MEDIA_INDEX_PATTERN = "evidence/local_media_indices/*.yaml"
VIDEO_TAKE_PATTERN = "visual_dev/omni_sets/SC*/video_takes.yaml"
VIDEO_REVIEW_PATTERN = "evidence/video_reviews/*.yaml"
SELECTED_TAKE_PATTERN = "visual_dev/omni_sets/SC*/selected_take.yaml"
AESTHETIC_BIBLE_PATH = "planning/aesthetic_bible.yaml"
SCENE_CLIP_MAP_PATH = "evidence/scene_clip_map.csv"

SCENE_CLIP_MAP_HEADER = [
    "scene_id",
    "selected_take",
    "prompt_id",
    "external_storage_ref",
    "platform_asset_ref",
    "local_proxy_ref",
    "repo_binary_committed",
    "lock_status",
]

FORBIDDEN_LIFECYCLE_KEYS = {"pack_status", "canon_lock", "approved", "locked"}
PACK_SUGGESTION_REQUIRED_KEYS = {
    "element_id",
    "suggested_field",
    "suggested_value",
    "reason",
    "applied_by",
    "applied_at",
}
PACK_SUGGESTION_ALLOWED_VALUES = {"metadata_only", "seeded"}
PROMPT_REVIEW_REQUIRED_KEYS = {"source_prompt_id", "corrected_brief"}
AGENT_HANDOFF_BRANCH_RE = re.compile(r"^(main$|feat/|fix/|docs/|chore/|review/)")
AGENT_HANDOFF_HEAD_SHA_RE = re.compile(r"^[A-Fa-f0-9]{7,40}$")
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[/\\]")


@dataclass
class ProductionValidationIssue:
    file: str
    record_type: str
    field_path: str
    message: str


@dataclass
class ProductionValidationReport:
    total_files: int
    valid_files: int
    invalid_files: int
    by_record_type: dict[str, int]
    issues: list[ProductionValidationIssue]

    @property
    def has_errors(self) -> bool:
        return self.invalid_files > 0


def load_schema(schema_path: Path) -> dict[str, Any]:
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def collect_production_files(repo_root: Path) -> dict[str, list[Path]]:
    """Return production metadata YAML files grouped by validation target."""
    return {
        "image_selection": sorted(repo_root.glob(IMAGE_SELECTION_PATTERN)),
        "asset_clearance": sorted(repo_root.glob(ASSET_CLEARANCE_PATTERN)),
        "pack_manifest_update_suggestion": sorted(repo_root.glob(PACK_SUGGESTION_PATTERN)),
        "prompt_review_brief": sorted(repo_root.glob(PROMPT_REVIEW_BRIEF_PATTERN)),
        "storyboard_options": sorted(repo_root.glob(STORYBOARD_OPTIONS_PATTERN)),
        "shot_list_omni_suggestion": sorted(
            repo_root.glob(SHOT_LIST_OMNI_SUGGESTION_PATTERN)
        ),
        "batch_job": sorted(repo_root.glob(BATCH_JOB_PATTERN)),
        "operator_session": sorted(repo_root.glob(OPERATOR_SESSION_PATTERN)),
        "agent_handoff": sorted(repo_root.glob(AGENT_HANDOFF_PATTERN)),
        "local_media_index": sorted(repo_root.glob(LOCAL_MEDIA_INDEX_PATTERN)),
        "video_take": sorted(repo_root.glob(VIDEO_TAKE_PATTERN)),
        "video_review": sorted(repo_root.glob(VIDEO_REVIEW_PATTERN)),
        "selected_take": sorted(repo_root.glob(SELECTED_TAKE_PATTERN)),
        "aesthetic_bible": (
            [repo_root / AESTHETIC_BIBLE_PATH]
            if (repo_root / AESTHETIC_BIBLE_PATH).is_file()
            else []
        ),
        "scene_clip_map": [repo_root / SCENE_CLIP_MAP_PATH]
        if (repo_root / SCENE_CLIP_MAP_PATH).exists()
        or list(repo_root.glob(SELECTED_TAKE_PATTERN))
        else [],
    }


def _schema_issues(
    *,
    path: Path,
    repo_root: Path,
    record_type: str,
    validator: Draft202012Validator,
) -> list[ProductionValidationIssue]:
    issues: list[ProductionValidationIssue] = []

    try:
        data = load_yaml_file(path)
    except Exception as exc:
        return [
            ProductionValidationIssue(
                file=_relative(path, repo_root),
                record_type=record_type,
                field_path="",
                message=f"YAML parse error: {exc}",
            )
        ]

    if data is None:
        return [
            ProductionValidationIssue(
                file=_relative(path, repo_root),
                record_type=record_type,
                field_path="",
                message="File is empty or contains only comments.",
            )
        ]

    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        issues.append(
            ProductionValidationIssue(
                file=_relative(path, repo_root),
                record_type=record_type,
                field_path=field_path,
                message=error.message,
            )
        )

    if isinstance(data, dict):
        forbidden = sorted(FORBIDDEN_LIFECYCLE_KEYS & set(data))
        for key in forbidden:
            issues.append(
                ProductionValidationIssue(
                    file=_relative(path, repo_root),
                    record_type=record_type,
                    field_path=key,
                    message="Lifecycle state must not be set directly in production metadata.",
                )
            )

    return issues


def _load_structural_record(
    *,
    path: Path,
    repo_root: Path,
    record_type: str,
) -> tuple[Any | None, list[ProductionValidationIssue]]:
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        return None, [
            ProductionValidationIssue(
                file=_relative(path, repo_root),
                record_type=record_type,
                field_path="",
                message=f"YAML parse error: {exc}",
            )
        ]

    if not isinstance(data, dict):
        return data, [
            ProductionValidationIssue(
                file=_relative(path, repo_root),
                record_type=record_type,
                field_path="(root)",
                message="Record must be a mapping.",
            )
        ]
    return data, []


def _structural_issue(
    *,
    path: Path,
    repo_root: Path,
    record_type: str,
    field_path: str,
    message: str,
) -> ProductionValidationIssue:
    return ProductionValidationIssue(
        file=_relative(path, repo_root),
        record_type=record_type,
        field_path=field_path,
        message=message,
    )


def validate_pack_suggestion_file(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Validate a pack manifest suggestion without mutating pack_manifest.yaml."""
    record_type = "pack_manifest_update_suggestion"
    data, issues = _load_structural_record(
        path=path,
        repo_root=repo_root,
        record_type=record_type,
    )
    if issues:
        return issues

    missing = sorted(PACK_SUGGESTION_REQUIRED_KEYS - set(data))
    for key in missing:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path=key,
                message="Required field is missing.",
            )
        )

    forbidden = sorted(FORBIDDEN_LIFECYCLE_KEYS & set(data))
    for key in forbidden:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path=key,
                message="Lifecycle state must not be set directly in a suggestion record.",
            )
        )

    if data.get("suggested_field") != "pack_status":
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="suggested_field",
                message='suggested_field must be "pack_status".',
            )
        )

    if data.get("suggested_value") not in PACK_SUGGESTION_ALLOWED_VALUES:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="suggested_value",
                message=(
                    "suggested_value must be metadata_only or seeded; "
                    "approval/lock promotion is out of Batch 5.6 scope."
                ),
            )
        )

    reason = data.get("reason")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="reason",
                message="reason must be a non-empty string.",
            )
        )

    return issues


def validate_prompt_review_brief_file(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Validate a corrected prompt brief produced from image review feedback."""
    record_type = "prompt_review_brief"
    data, issues = _load_structural_record(
        path=path,
        repo_root=repo_root,
        record_type=record_type,
    )
    if issues:
        return issues

    missing = sorted(PROMPT_REVIEW_REQUIRED_KEYS - set(data))
    for key in missing:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path=key,
                message="Required field is missing.",
            )
        )

    source_prompt_id = data.get("source_prompt_id")
    if source_prompt_id is not None:
        if not isinstance(source_prompt_id, str) or not source_prompt_id:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path="source_prompt_id",
                    message="source_prompt_id must be a non-empty string.",
                )
            )

    corrected_brief = data.get("corrected_brief")
    if corrected_brief is not None:
        if not isinstance(corrected_brief, dict) or not corrected_brief:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path="corrected_brief",
                    message="corrected_brief must be a non-empty mapping.",
                )
            )

    return issues


def _is_safe_handoff_context_path(value: str) -> bool:
    if value.startswith("/"):
        return False
    if WINDOWS_ABSOLUTE_PATH_RE.match(value):
        return False
    parts = value.replace("\\", "/").split("/")
    return ".." not in parts


def validate_agent_handoff_consistency(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Validate handoff rules that sit outside JSON Schema."""
    record_type = "agent_handoff"
    data, issues = _load_structural_record(
        path=path,
        repo_root=repo_root,
        record_type=record_type,
    )
    if issues:
        return issues

    if data.get("from_agent") == data.get("to_agent"):
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="to_agent",
                message="from_agent and to_agent must be different.",
            )
        )

    context_files = data.get("context_files")
    if isinstance(context_files, list):
        for index, context_path in enumerate(context_files):
            if isinstance(context_path, str) and not _is_safe_handoff_context_path(
                context_path
            ):
                issues.append(
                    _structural_issue(
                        path=path,
                        repo_root=repo_root,
                        record_type=record_type,
                        field_path=f"context_files.{index}",
                        message=(
                            "context_files entries must be repo-relative paths "
                            "with no absolute paths or traversal segments."
                        ),
                    )
                )

    head_sha = data.get("head_sha")
    if head_sha is not None and (
        not isinstance(head_sha, str) or not AGENT_HANDOFF_HEAD_SHA_RE.match(head_sha)
    ):
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="head_sha",
                message="head_sha must be 7 to 40 hex characters.",
            )
        )

    branch = data.get("branch")
    if branch is not None and (
        not isinstance(branch, str) or not AGENT_HANDOFF_BRANCH_RE.match(branch)
    ):
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="branch",
                message="branch must start with main, feat/, fix/, docs/, chore/, or review/.",
            )
        )

    return issues


def validate_video_take_consistency(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Validate cross-field video take rules that JSON Schema cannot express."""
    record_type = "video_take"
    data, issues = _load_structural_record(
        path=path,
        repo_root=repo_root,
        record_type=record_type,
    )
    if issues:
        return issues

    takes = data.get("takes")
    if not isinstance(takes, list):
        return issues

    selected_takes = [
        take for take in takes if isinstance(take, dict) and take.get("status") == "selected"
    ]
    if len(selected_takes) > 1:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="takes",
                message="At most one take may have status selected.",
            )
        )

    selected_take = data.get("selected_take")
    if selected_take is not None:
        matching_selected = [
            take
            for take in selected_takes
            if isinstance(take, dict) and take.get("take_id") == selected_take
        ]
        if not matching_selected:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path="selected_take",
                    message="selected_take must match a take_id whose status is selected.",
                )
            )
    elif selected_takes:
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="selected_take",
                message="selected_take must be set when a take has status selected.",
            )
        )

    for index, take in enumerate(takes):
        if not isinstance(take, dict):
            continue
        field_prefix = f"takes.{index}"
        if take.get("repo_binary_committed") is not False:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.repo_binary_committed",
                    message="repo_binary_committed must be false for every video take.",
                )
            )
        external_storage_ref = take.get("external_storage_ref")
        missing_external_allowed = (
            take.get("status") == "candidate"
            and take.get("storage_status") == "pending_external"
        )
        if not external_storage_ref and not missing_external_allowed:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.external_storage_ref",
                    message=(
                        "external_storage_ref is required unless the take is a "
                        "candidate with storage_status pending_external."
                    ),
                )
            )

    return issues


_VIDEO_BINARY_EXTENSIONS = {".mp4", ".mov", ".mkv", ".wav"}


def _looks_like_repo_video_binary(value: object) -> bool:
    if not value:
        return False
    text = str(value)
    if "://" in text:
        return False
    return Path(text).suffix.lower() in _VIDEO_BINARY_EXTENSIONS


def validate_selected_take_extra(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Cross-field checks for selected_take.yaml beyond JSON Schema."""
    issues: list[ProductionValidationIssue] = []
    try:
        data = load_yaml_file(path)
    except Exception:
        return issues
    if not isinstance(data, dict):
        return issues
    local_proxy_ref = data.get("local_proxy_ref")
    if _looks_like_repo_video_binary(local_proxy_ref):
        issues.append(
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type="selected_take",
                field_path="local_proxy_ref",
                message=(
                    "local_proxy_ref must not point to a repo video binary. "
                    "Use an external storage ref (dvc://, s3://, etc.) or null."
                ),
            )
        )
    return issues


def validate_local_media_index_extra(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Cross-field checks for local_media_index beyond JSON Schema."""
    record_type = "local_media_index"
    data, issues = _load_structural_record(
        path=path,
        repo_root=repo_root,
        record_type=record_type,
    )
    if issues:
        return issues

    entries = data.get("entries")
    if not isinstance(entries, list):
        return issues

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        field_prefix = f"entries.{index}"

        if entry.get("repo_binary_committed") is not False:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.repo_binary_committed",
                    message="repo_binary_committed must be false for every media index entry.",
                )
            )

        local_path = entry.get("local_path")
        if _looks_like_repo_video_binary(local_path) and not entry.get("external_storage_ref"):
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.external_storage_ref",
                    message=(
                        "Video-like local_path must also have external_storage_ref "
                        "to ensure the master copy is tracked in external storage."
                    ),
                )
            )

    return issues


def validate_scene_clip_map_file(
    path: Path,
    repo_root: Path,
) -> list[ProductionValidationIssue]:
    """Validate the metadata-only scene clip map CSV."""
    record_type = "scene_clip_map"
    issues: list[ProductionValidationIssue] = []
    if not path.exists():
        return [
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="",
                message="scene_clip_map.csv is required when selected_take.yaml exists.",
            )
        ]
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != SCENE_CLIP_MAP_HEADER:
                return [
                    _structural_issue(
                        path=path,
                        repo_root=repo_root,
                        record_type=record_type,
                        field_path="header",
                        message="scene_clip_map.csv header is invalid.",
                    )
                ]
            rows = list(reader)
    except Exception as exc:
        return [
            _structural_issue(
                path=path,
                repo_root=repo_root,
                record_type=record_type,
                field_path="",
                message=f"CSV parse error: {exc}",
            )
        ]

    seen_scene_rows: dict[str, dict[str, str]] = {}
    for index, row in enumerate(rows):
        scene_id = row.get("scene_id", "")
        field_prefix = f"rows.{index}"
        if not scene_id:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.scene_id",
                    message="scene_id is required.",
                )
            )
            continue
        selected_path = (
            repo_root / "visual_dev" / "omni_sets" / scene_id / "selected_take.yaml"
        )
        if not selected_path.exists():
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.scene_id",
                    message="scene_clip_map row requires matching selected_take.yaml.",
                )
            )
        if scene_id in seen_scene_rows and seen_scene_rows[scene_id] != row:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.scene_id",
                    message="Duplicate scene_id rows must be identical.",
                )
            )
        seen_scene_rows[scene_id] = row
        if not row.get("selected_take"):
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.selected_take",
                    message="selected_take is required.",
                )
            )
        if not row.get("external_storage_ref"):
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.external_storage_ref",
                    message="external_storage_ref is required.",
                )
            )
        if row.get("repo_binary_committed") != "false":
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path=f"{field_prefix}.repo_binary_committed",
                    message='repo_binary_committed must be "false".',
                )
            )

    selected_take_files = sorted(repo_root.glob(SELECTED_TAKE_PATTERN))
    mapped_scene_ids = set(seen_scene_rows)
    for selected_path in selected_take_files:
        scene_id = selected_path.parent.name
        if scene_id not in mapped_scene_ids:
            issues.append(
                _structural_issue(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    field_path="scene_id",
                    message=f"Missing scene_clip_map row for {scene_id}.",
                )
            )

    return issues


def run_validation(
    repo_root: Path,
    report_json: Path | None = None,
) -> ProductionValidationReport:
    """Run production metadata validation."""
    image_selection_schema = load_schema(repo_root / "schemas" / "image_selection.schema.json")
    asset_clearance_schema = load_schema(repo_root / "schemas" / "asset_clearance.schema.json")
    storyboard_options_schema = load_schema(
        repo_root / "schemas" / "storyboard_option.schema.json"
    )
    batch_job_schema = load_schema(repo_root / "schemas" / "batch_job.schema.json")
    image_selection_validator = Draft202012Validator(image_selection_schema)
    asset_clearance_validator = Draft202012Validator(asset_clearance_schema)
    storyboard_options_validator = Draft202012Validator(storyboard_options_schema)
    shot_list_omni_suggestion_schema = load_schema(
        repo_root / "schemas" / "shot_list_omni_suggestion.schema.json"
    )
    batch_job_validator = Draft202012Validator(batch_job_schema)
    shot_list_omni_suggestion_validator = Draft202012Validator(
        shot_list_omni_suggestion_schema
    )
    operator_session_validator: Draft202012Validator | None = None
    agent_handoff_validator: Draft202012Validator | None = None
    local_media_index_validator: Draft202012Validator | None = None
    video_take_validator: Draft202012Validator | None = None
    video_review_validator: Draft202012Validator | None = None
    selected_take_validator: Draft202012Validator | None = None
    aesthetic_bible_validator: Draft202012Validator | None = None

    grouped_files = collect_production_files(repo_root)
    total = sum(len(files) for files in grouped_files.values())
    by_record_type = {record_type: len(files) for record_type, files in grouped_files.items()}

    all_issues: list[ProductionValidationIssue] = []
    invalid_count = 0

    for record_type, files in grouped_files.items():
        for path in files:
            if record_type == "image_selection":
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=image_selection_validator,
                )
            elif record_type == "asset_clearance":
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=asset_clearance_validator,
                )
            elif record_type == "pack_manifest_update_suggestion":
                file_issues = validate_pack_suggestion_file(path, repo_root)
            elif record_type == "prompt_review_brief":
                file_issues = validate_prompt_review_brief_file(path, repo_root)
            elif record_type == "storyboard_options":
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=storyboard_options_validator,
                )
            elif record_type == "shot_list_omni_suggestion":
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=shot_list_omni_suggestion_validator,
                )
            elif record_type == "batch_job":
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=batch_job_validator,
                )
            elif record_type == "operator_session":
                if operator_session_validator is None:
                    operator_session_schema = load_schema(
                        repo_root / "schemas" / "operator_session.schema.json"
                    )
                    operator_session_validator = Draft202012Validator(
                        operator_session_schema
                    )
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=operator_session_validator,
                )
            elif record_type == "agent_handoff":
                if agent_handoff_validator is None:
                    agent_handoff_schema = load_schema(
                        repo_root / "schemas" / "agent_handoff.schema.json"
                    )
                    agent_handoff_validator = Draft202012Validator(
                        agent_handoff_schema
                    )
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=agent_handoff_validator,
                )
                file_issues.extend(validate_agent_handoff_consistency(path, repo_root))
            elif record_type == "local_media_index":
                if local_media_index_validator is None:
                    local_media_index_schema = load_schema(
                        repo_root / "schemas" / "local_media_index.schema.json"
                    )
                    local_media_index_validator = Draft202012Validator(
                        local_media_index_schema
                    )
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=local_media_index_validator,
                )
                file_issues.extend(validate_local_media_index_extra(path, repo_root))
            elif record_type == "video_take":
                if video_take_validator is None:
                    video_take_schema = load_schema(
                        repo_root / "schemas" / "video_take.schema.json"
                    )
                    video_take_validator = Draft202012Validator(video_take_schema)
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=video_take_validator,
                )
                file_issues.extend(validate_video_take_consistency(path, repo_root))
            elif record_type == "video_review":
                if video_review_validator is None:
                    video_review_schema = load_schema(
                        repo_root / "schemas" / "video_review.schema.json"
                    )
                    video_review_validator = Draft202012Validator(video_review_schema)
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=video_review_validator,
                )
            elif record_type == "selected_take":
                if selected_take_validator is None:
                    selected_take_schema = load_schema(
                        repo_root / "schemas" / "selected_take.schema.json"
                    )
                    selected_take_validator = Draft202012Validator(selected_take_schema)
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=selected_take_validator,
                )
                file_issues.extend(validate_selected_take_extra(path, repo_root))
            elif record_type == "aesthetic_bible":
                if aesthetic_bible_validator is None:
                    aesthetic_bible_schema = load_schema(
                        repo_root / "schemas" / "aesthetic_bible.schema.json"
                    )
                    aesthetic_bible_validator = Draft202012Validator(
                        aesthetic_bible_schema
                    )
                file_issues = _schema_issues(
                    path=path,
                    repo_root=repo_root,
                    record_type=record_type,
                    validator=aesthetic_bible_validator,
                )
            elif record_type == "scene_clip_map":
                file_issues = validate_scene_clip_map_file(path, repo_root)
            else:
                file_issues = [
                    ProductionValidationIssue(
                        file=_relative(path, repo_root),
                        record_type=record_type,
                        field_path="",
                        message=f"Unsupported record type: {record_type}",
                    )
                ]

            if file_issues:
                invalid_count += 1
                all_issues.extend(file_issues)

    report = ProductionValidationReport(
        total_files=total,
        valid_files=total - invalid_count,
        invalid_files=invalid_count,
        by_record_type=by_record_type,
        issues=all_issues,
    )

    if report_json is not None:
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "total_files": report.total_files,
            "valid_files": report.valid_files,
            "invalid_files": report.invalid_files,
            "by_record_type": report.by_record_type,
            "issues": [asdict(i) for i in report.issues],
        }
        with report_json.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    return report


def print_report(report: ProductionValidationReport) -> None:
    if report.total_files == 0:
        print("0 files validated - no production metadata YAML files found.")
        return

    print(f"Production record validation: {report.total_files} files scanned.")
    print(f"  Valid:   {report.valid_files}")
    print(f"  Invalid: {report.invalid_files}")
    print("  By type:")
    for record_type, count in sorted(report.by_record_type.items()):
        print(f"    {record_type}: {count}")

    if report.issues:
        print()
        print("Validation errors:")
        for issue in report.issues:
            print(
                f"  [{issue.file}] {issue.record_type} "
                f"{issue.field_path}: {issue.message}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate production metadata YAML/CSV records."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory).",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Path to write JSON validation report (optional).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    report_json = args.report_json.resolve() if args.report_json else None

    report = run_validation(repo_root=repo_root, report_json=report_json)
    print_report(report)

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
