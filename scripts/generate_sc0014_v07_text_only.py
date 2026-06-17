"""
generate_sc0014_v07_text_only.py

SC0014 v07 text-only literal multi-shot generation + idempotent migration.

The v06 Anchor & Animate route (22 designed stills -> 8 contact sheets ->
anchored_i2v Kling) is retired for SC0014. This script:

  1. Generates 8 Kling Omni prompt records directly as text_only multi-shot
     prompts under language_profile=kling_literal_alias_locked (version 7),
     writing to prompts/draft/ and run records to evidence/prompt_runs/.
  2. Deprecates the v06 SC0014 still/contact/anchored prompt records (draft
     files), and their rows in prompts/prompt_library.yaml and
     evidence/scene_prompt_map.csv.
  3. Upserts the 8 v07 rows into the library + scene map.

It is idempotent: re-running marks the same rows deprecated and upserts the
same v07 rows without duplicating. No live Kling call; metadata only.

Usage:
    python scripts/generate_sc0014_v07_text_only.py [--repo-root .] [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path
from typing import Any

import yaml

from scripts.agents.adapters.kling_omni import KlingOmniAdapter

_SCENE_ID = "SC0014"
_LANGUAGE_PROFILE = "kling_literal_alias_locked"
_VERSION = 7

# v06 prompt_ids retired for SC0014 (still 22 + contact 8 + anchored omni 8).
_V06_STILL_IDS = [f"SC0014__still-{i:02d}__v01" for i in range(1, 23)]
_V06_CONTACT_IDS = [f"SC0014__contact-clip-{i:02d}__v01" for i in range(1, 9)]
_V06_OMNI_IDS = [
    f"SC0014__omni-kling-omni-clip-clip-sc0014-{i:02d}-safe__v01" for i in range(1, 9)
]
_V06_RETIRED_IDS = set(_V06_STILL_IDS + _V06_CONTACT_IDS + _V06_OMNI_IDS)


def _write_yaml(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    content = yaml.dump(data, allow_unicode=True, sort_keys=False, width=120)
    if dry_run:
        print(f"# [dry-run] {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _generate_v07_records(repo_root: Path, dry_run: bool) -> list[dict[str, Any]]:
    draft_dir = repo_root / "prompts" / "draft"
    runs_dir = repo_root / "evidence" / "prompt_runs"
    adapter = KlingOmniAdapter(repo_root=repo_root, model_guidance_mode="dynamic_snapshot")
    manifests_dir = repo_root / "planning" / "scenes" / _SCENE_ID / "manifests"
    manifest_paths = sorted(manifests_dir.glob("CLIP_*.yaml"))

    records: list[dict[str, Any]] = []
    print("\n=== Generating 8 v07 text_only literal Kling prompts ===")
    for manifest_path in manifest_paths:
        result = adapter.generate_from_clip_manifest(
            manifest_path,
            version=_VERSION,
            input_mode="text_only",
            language_profile=_LANGUAGE_PROFILE,
            variant_mode="safe",
            render_pass="visual_test",
            quality_tier="test_720p",
        )
        record = result.prompt_record
        records.append(record)
        prompt_id = record["prompt_id"]
        _write_yaml(draft_dir / f"{prompt_id}.yaml", record, dry_run)
        _write_yaml(runs_dir / f"{result.run_record['run_id']}.yaml", result.run_record, dry_run)
        flag = " (warnings)" if result.warnings else ""
        print(f"  {prompt_id}: {len(record['prompt_text'])} chars{flag}")
        for w in result.warnings:
            print(f"    WARNING: {w}")
    return records


def _deprecate_draft_files(repo_root: Path, dry_run: bool) -> int:
    """Set lifecycle_stage/status=deprecated on each retired v06 draft record."""
    draft_dir = repo_root / "prompts" / "draft"
    count = 0
    for pid in sorted(_V06_RETIRED_IDS):
        path = draft_dir / f"{pid}.yaml"
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        changed = False
        if data.get("lifecycle_stage") != "deprecated":
            data["lifecycle_stage"] = "deprecated"
            changed = True
        if data.get("status") not in (None, "deprecated") and data.get("status") != "deprecated":
            data["status"] = "deprecated"
            changed = True
        if changed and not dry_run:
            path.write_text(
                yaml.dump(data, allow_unicode=True, sort_keys=False, width=120),
                encoding="utf-8",
            )
        count += int(changed)
    print(f"\nDeprecated v06 draft records: {count} updated "
          f"({len(_V06_RETIRED_IDS)} in retired set)")
    return count


def _v07_omni_id(clip_index: int) -> str:
    return (
        f"SC0014__omni-kling-omni-clip-clip-sc0014-{clip_index:02d}-safe__v{_VERSION:02d}"
    )


def _update_prompt_library(repo_root: Path, dry_run: bool) -> None:
    path = repo_root / "prompts" / "prompt_library.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    prompts: list[dict[str, Any]] = data.get("prompts") or []

    # 1. Deprecate retired v06 rows.
    for row in prompts:
        if row.get("prompt_id") in _V06_RETIRED_IDS:
            row["lifecycle_stage"] = "deprecated"

    # 2. Upsert v07 omni rows (idempotent).
    existing_ids = {row.get("prompt_id") for row in prompts}
    for i in range(1, 9):
        pid = _v07_omni_id(i)
        if pid in existing_ids:
            continue
        prompts.append({
            "prompt_id": pid,
            "scene_id": _SCENE_ID,
            "prompt_type": "omni_instruction",
            "lifecycle_stage": "draft",
            "target_models": ["kling_omni"],
        })

    data["prompts"] = prompts
    if not dry_run:
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
    print("Updated prompt_library.yaml (v06 deprecated, v07 upserted)")


def _update_scene_prompt_map(repo_root: Path, dry_run: bool) -> None:
    path = repo_root / "evidence" / "scene_prompt_map.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    # 1. Deprecate retired v06 rows.
    for row in rows:
        if row.get("prompt_id") in _V06_RETIRED_IDS:
            row["lifecycle_stage"] = "deprecated"

    # 2. Upsert v07 omni rows (idempotent).
    existing_ids = {row.get("prompt_id") for row in rows}
    for i in range(1, 9):
        pid = _v07_omni_id(i)
        if pid in existing_ids:
            continue
        rows.append({
            "scene_id": _SCENE_ID,
            "prompt_id": pid,
            "prompt_type": "omni_instruction",
            "lifecycle_stage": "draft",
            "target_model": "kling_omni",
            "asset_ref": "pending_generation",
            "article3_flag": "",
            "notes": f"v07 text-only literal kling_literal_alias_locked prompt for CLIP_SC0014_{i:02d}",
        })

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    if not dry_run:
        path.write_text(buf.getvalue(), encoding="utf-8", newline="")
    print("Updated scene_prompt_map.csv (v06 deprecated, v07 upserted)")


def generate(repo_root: Path, dry_run: bool = False) -> None:
    records = _generate_v07_records(repo_root, dry_run)
    _deprecate_draft_files(repo_root, dry_run)
    _update_prompt_library(repo_root, dry_run)
    _update_scene_prompt_map(repo_root, dry_run)
    print(f"\nTotal v07 records: {len(records)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SC0014 v07 text-only literal prompts.")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--dry-run", action="store_true", help="Generate without writing files")
    args = parser.parse_args()
    generate(repo_root=Path(args.repo_root).resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
