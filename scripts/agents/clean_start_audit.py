"""
Build a metadata-only clean-start audit before first canonical asset intake.

B8-0 records the scientific pre-asset baseline after the v0.3.0 Zenodo
publication checkpoint. It never creates assets, mutates pack manifests,
promotes lifecycle state, locks packs, or runs external generation.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


DEFAULT_AUDIT_AT = "2026-05-05T11:15:00Z"
DEFAULT_STORAGE_POLICY = "no_binary_commits"
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


class CleanStartAuditError(RuntimeError):
    """Raised when a clean-start audit cannot be built."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)


def _git_tracked_files(repo_root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [repo_root / line for line in result.stdout.splitlines() if line.strip()]


def _tracked_media_files(repo_root: Path) -> list[str]:
    return sorted(
        path.relative_to(repo_root).as_posix()
        for path in _git_tracked_files(repo_root)
        if path.suffix.lower() in MEDIA_EXTENSIONS
    )


def _canonical_asset_paths(repo_root: Path) -> list[str]:
    """Return committed canonical asset references before first intake."""

    committed_refs: list[str] = []
    for slot_path in sorted(repo_root.glob("visual_dev/elements/**/intake_slot.yaml")):
        slot = _read_yaml(slot_path)
        if isinstance(slot, dict):
            refs = slot.get("canonical_assets_committed")
            if isinstance(refs, list):
                committed_refs.extend(str(ref) for ref in refs if ref)

    media_refs = [
        rel
        for rel in _tracked_media_files(repo_root)
        if rel.startswith("visual_dev/elements/")
    ]
    return sorted(set(committed_refs + media_refs))


def _load_required_records(repo_root: Path, scene_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    gate_ref = repo_root / "evidence" / "omni_set_gates" / f"{scene_id}_gate.yaml"
    readiness_ref = (
        repo_root
        / "evidence"
        / "pack_lock_readiness"
        / f"{scene_id}_pack_lock_readiness.yaml"
    )
    gate = _read_yaml(gate_ref)
    readiness = _read_yaml(readiness_ref)
    if not isinstance(gate, dict):
        raise CleanStartAuditError(f"Missing Omni set gate record: {gate_ref}")
    if not isinstance(readiness, dict):
        raise CleanStartAuditError(f"Missing pack readiness record: {readiness_ref}")
    return gate, readiness


def build_clean_start_audit(
    repo_root: str | Path,
    scene_id: str,
    *,
    audit_at: str = DEFAULT_AUDIT_AT,
) -> dict[str, Any]:
    """Return the deterministic B8-0 clean pre-asset baseline audit."""

    root = Path(repo_root)
    gate, readiness = _load_required_records(root, scene_id)
    tracked_media = _tracked_media_files(root)
    canonical_assets = _canonical_asset_paths(root)
    packs = readiness.get("packs") or []
    metadata_only_pack_count = sum(
        1 for pack in packs if isinstance(pack, dict) and pack.get("pack_status") == "metadata_only"
    )

    return {
        "scene_id": scene_id,
        "audit_at": audit_at,
        "audit_status": "clean_pre_asset_baseline",
        "ready_for_first_asset_intake": True,
        "blocked_for_kling_generation": gate.get("ready_for_kling_prompt_generation")
        is False,
        "summary": {
            "tracked_media_binaries_found": bool(tracked_media),
            "tracked_media_binary_count": len(tracked_media),
            "canonical_assets_present": bool(canonical_assets),
            "canonical_asset_count": len(canonical_assets),
            "external_generation_performed": False,
            "pack_locking_performed": False,
            "pack_manifest_mutation_performed": False,
            "copyright_completion_claimed": False,
            "provenance_completion_claimed": False,
            "lifecycle_promotion_performed": False,
        },
        "publication_checkpoint": {
            "public_release_version": "v0.3.0",
            "zenodo_doi": "10.5281/zenodo.20036189",
            "zenodo_record": "https://zenodo.org/records/20036189",
            "citation_updated": True,
        },
        "baseline_refs": {
            "omni_gate": f"evidence/omni_set_gates/{scene_id}_gate.yaml",
            "pack_lock_readiness": (
                f"evidence/pack_lock_readiness/{scene_id}_pack_lock_readiness.yaml"
            ),
            "intake_instructions": (
                "evidence/canonical_asset_intake_instructions/"
                f"{scene_id}_intake_instructions.yaml"
            ),
        },
        "sc0001_gate_state": {
            "ready_for_kling_prompt_generation": gate.get(
                "ready_for_kling_prompt_generation"
            ),
            "gate_status": gate.get("gate_status"),
            "ready_packs": (
                gate.get("element_pack_gate", {})
                .get("summary", {})
                .get("ready_packs")
            ),
            "metadata_only_packs": (
                gate.get("element_pack_gate", {})
                .get("summary", {})
                .get("metadata_only_packs")
            ),
        },
        "pack_baseline": {
            "required_pack_count": len(packs),
            "metadata_only_pack_count": metadata_only_pack_count,
            "ready_for_lock_review": readiness.get("summary", {}).get(
                "ready_for_lock_review"
            ),
            "packs_missing_canonical_assets": readiness.get("summary", {}).get(
                "packs_missing_canonical_assets"
            ),
        },
        "tracked_media_binaries": tracked_media,
        "canonical_assets_committed": canonical_assets,
        "local_non_baseline_artifacts": [
            {
                "path": "evidence/provenance/dryrun-z1p1/",
                "status": "ignored_local_artifact",
                "part_of_first_asset_intake": False,
                "affects_repo_baseline": False,
            },
            {
                "path": ".claude/worktrees/",
                "status": "ignored_local_worktree_artifact",
                "part_of_first_asset_intake": False,
                "affects_repo_baseline": False,
            },
            {
                "path": "prompts/prompt_library.yaml",
                "status": "local_dirty_tracked_file",
                "staged_for_this_batch": False,
                "touched_by_this_batch": False,
                "part_of_first_asset_intake": False,
                "affects_repo_baseline": False,
            },
        ],
        "storage_policy": DEFAULT_STORAGE_POLICY,
        "external_generation_performed": False,
        "binary_outputs_created": False,
        "pack_locking_performed": False,
        "pack_manifest_mutation_performed": False,
        "copyright_completion_claimed": False,
        "provenance_completion_claimed": False,
        "lifecycle_promotion_performed": False,
    }


def write_clean_start_audit(
    repo_root: str | Path,
    scene_id: str,
    *,
    output_path: str | Path | None = None,
    audit_at: str = DEFAULT_AUDIT_AT,
) -> Path:
    """Write the clean-start audit record."""

    root = Path(repo_root)
    report = build_clean_start_audit(root, scene_id, audit_at=audit_at)
    out_path = (
        Path(output_path)
        if output_path is not None
        else root / "evidence" / "clean_start_audits" / f"{scene_id}_pre_asset_start.yaml"
    )
    _write_yaml(out_path, report)
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--audit-at", default=DEFAULT_AUDIT_AT)
    args = parser.parse_args(argv)

    write_clean_start_audit(
        args.repo_root,
        args.scene_id,
        output_path=args.output_path,
        audit_at=args.audit_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
