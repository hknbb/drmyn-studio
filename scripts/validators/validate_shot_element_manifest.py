"""Semantic validation for shot_element_manifest records.

The schema validates structure. This module checks cross-record readiness:
required elements must have a scene binding, a created-or-better Kling state,
and a review-or-better kling_element_reference record before Kling prompt
synthesis may treat them as attached elements.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ACTIVE_STATUSES = {"created", "voice_capable", "voice_locked"}
STATUS_ORDER = {"created": 1, "voice_capable": 2, "voice_locked": 3}
REFERENCE_READY_STATUSES = {"review", "approved", "locked", "materialized"}
FORBIDDEN_LIFECYCLE_KEYS = {"pack_status", "canon_lock", "approved", "locked"}
LOC_SUBAREA_RE = re.compile(r"^(LOC\d{3})_([A-Z0-9_]+)$")


@dataclass(frozen=True)
class ShotElementManifestIssue:
    file: str
    field_path: str
    message: str


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_mapping(path: Path) -> dict[str, Any] | None:
    try:
        data = _load_yaml(path)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _schema_issues(path: Path, repo_root: Path) -> list[ShotElementManifestIssue]:
    schema_path = repo_root / "schemas" / "shot_element_manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    try:
        data = _load_yaml(path)
    except Exception as exc:
        return [
            ShotElementManifestIssue(
                file=_relative(path, repo_root),
                field_path="",
                message=f"YAML parse error: {exc}",
            )
        ]

    issues: list[ShotElementManifestIssue] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        issues.append(
            ShotElementManifestIssue(
                file=_relative(path, repo_root),
                field_path=".".join(str(p) for p in error.absolute_path) or "(root)",
                message=error.message,
            )
        )
    return issues


def _load_scene_bindings(repo_root: Path, scene_id: str) -> dict[str, dict[str, Any]]:
    path = repo_root / "visual_dev" / "omni_sets" / scene_id / "element_bindings.yaml"
    if not path.exists():
        return {}
    bindings: dict[str, dict[str, Any]] = {}
    try:
        with path.open("r", encoding="utf-8") as f:
            for doc in yaml.safe_load_all(f):
                if not isinstance(doc, dict):
                    continue
                element_id = doc.get("element_id")
                if isinstance(element_id, str) and element_id:
                    bindings[element_id] = doc
    except Exception:
        return bindings
    return bindings


def _element_root(repo_root: Path, element_id: str, element_type: str) -> Path:
    if element_type == "character":
        return repo_root / "visual_dev" / "elements" / "characters" / element_id
    if element_type == "prop":
        return repo_root / "visual_dev" / "elements" / "props" / element_id
    if element_type == "location":
        return repo_root / "visual_dev" / "elements" / "locations" / element_id
    if element_type == "location_sub_area":
        match = LOC_SUBAREA_RE.match(element_id)
        if match:
            location_id = match.group(1)
            sub_area = match.group(2).lower()
            return (
                repo_root
                / "visual_dev"
                / "elements"
                / "locations"
                / location_id
                / "sub_areas"
                / sub_area
            )
        return repo_root / "visual_dev" / "elements" / "locations" / element_id
    if element_type == "wardrobe":
        return repo_root / "planning" / "wardrobe" / element_id
    return repo_root / "visual_dev" / "elements" / element_type / element_id


def _element_root_from_binding(
    repo_root: Path,
    element_id: str,
    element_type: str,
    binding: dict[str, Any] | None,
) -> Path:
    if element_type == "location_sub_area" and binding:
        ref = binding.get("source_element_view_plan_ref")
        if isinstance(ref, str) and ref.strip():
            ref_path = repo_root / ref
            if ref_path.name == "element_view_plan.yaml":
                return ref_path.parent
    return _element_root(repo_root, element_id, element_type)


def _find_kling_reference(root: Path) -> Path:
    return root / "kling_element_reference.yaml"


def _find_gpt_images_pack(root: Path) -> Path:
    return root / "gpt_images_perspective_pack.yaml"


def _find_pack_manifest(root: Path) -> Path:
    return root / "pack_manifest.yaml"


def _binding_satisfies(actual: str | None, required: str) -> bool:
    if actual not in STATUS_ORDER or required not in STATUS_ORDER:
        return False
    return STATUS_ORDER[actual] >= STATUS_ORDER[required]


def validate_shot_element_manifest_file(
    path: Path,
    repo_root: Path,
) -> list[ShotElementManifestIssue]:
    """Validate one shot_element_manifest file."""
    issues = _schema_issues(path, repo_root)
    data = _load_mapping(path)
    if issues or not data:
        return issues

    rel_file = _relative(path, repo_root)
    forbidden = sorted(FORBIDDEN_LIFECYCLE_KEYS & set(data))
    for key in forbidden:
        issues.append(
            ShotElementManifestIssue(
                file=rel_file,
                field_path=key,
                message="Lifecycle state keys are forbidden in shot element manifests.",
            )
        )

    scene_id = str(data.get("scene_id") or "")
    bindings = _load_scene_bindings(repo_root, scene_id)
    required_elements = data.get("required_elements") or []
    environmental_allowed = set(data.get("environmental_only_allowed_ids") or [])

    if not required_elements:
        computed_gate = "pending"
    else:
        computed_gate = "all_elements_ready"

    for index, element in enumerate(required_elements):
        if not isinstance(element, dict):
            continue
        prefix = f"required_elements[{index}]"
        element_id = str(element.get("element_id") or "")
        element_type = str(element.get("element_type") or "")
        required_state = str(element.get("registration_state_required") or "")
        role = str(element.get("role") or "")
        binding = bindings.get(element_id)

        if element_id in environmental_allowed and role != "environmental_only":
            issues.append(
                ShotElementManifestIssue(
                    file=rel_file,
                    field_path=f"{prefix}.element_id",
                    message=(
                        f"{element_id} is listed as environmental-only but is also "
                        f"required as {role}."
                    ),
                )
            )

        if binding is None:
            issues.append(
                ShotElementManifestIssue(
                    file=rel_file,
                    field_path=f"{prefix}.element_id",
                    message=f"{element_id} has no matching element_binding for scene {scene_id}.",
                )
            )
            computed_gate = "blocked"
            root = _element_root(repo_root, element_id, element_type)
        else:
            actual_status = binding.get("binding_status")
            if actual_status not in ACTIVE_STATUSES:
                issues.append(
                    ShotElementManifestIssue(
                        file=rel_file,
                        field_path=f"{prefix}.registration_state_required",
                        message=(
                            f"{element_id} binding_status is {actual_status!r}; "
                            "required attached elements must be created or better."
                        ),
                    )
                )
                computed_gate = "blocked"
            elif not _binding_satisfies(str(actual_status), required_state):
                issues.append(
                    ShotElementManifestIssue(
                        file=rel_file,
                        field_path=f"{prefix}.registration_state_required",
                        message=(
                            f"{element_id} binding_status {actual_status!r} does not "
                            f"satisfy required state {required_state!r}."
                        ),
                    )
                )
                computed_gate = "blocked"
            root = _element_root_from_binding(repo_root, element_id, element_type, binding)

        pack_manifest = _find_pack_manifest(root)
        gpt_pack = _find_gpt_images_pack(root)
        kling_ref = _find_kling_reference(root)
        for field, candidate in (
            ("pack_manifest", pack_manifest),
            ("gpt_images_perspective_pack", gpt_pack),
            ("kling_element_reference", kling_ref),
        ):
            if not candidate.exists():
                issues.append(
                    ShotElementManifestIssue(
                        file=rel_file,
                        field_path=f"{prefix}.{field}",
                        message=f"{field} not found for {element_id}: {_relative(candidate, repo_root)}",
                    )
                )
                computed_gate = "blocked"

        ref_data = _load_mapping(kling_ref)
        if ref_data is not None:
            status = ref_data.get("status")
            if status not in REFERENCE_READY_STATUSES:
                issues.append(
                    ShotElementManifestIssue(
                        file=rel_file,
                        field_path=f"{prefix}.kling_element_reference.status",
                        message=(
                            f"{element_id} kling_element_reference status is {status!r}; "
                            "expected review or better."
                        ),
                    )
                )
                computed_gate = "blocked"

    declared_gate = data.get("gate_status")
    if declared_gate != computed_gate:
        issues.append(
            ShotElementManifestIssue(
                file=rel_file,
                field_path="gate_status",
                message=f"gate_status is {declared_gate!r}; computed gate_status is {computed_gate!r}.",
            )
        )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate shot element manifest records.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    all_issues: list[ShotElementManifestIssue] = []
    for raw_path in args.paths:
        path = raw_path if raw_path.is_absolute() else repo_root / raw_path
        all_issues.extend(validate_shot_element_manifest_file(path, repo_root))

    for issue in all_issues:
        print(f"{issue.file}:{issue.field_path}: {issue.message}")
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
