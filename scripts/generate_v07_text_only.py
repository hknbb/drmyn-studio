"""generate_v07_text_only.py

Generic v07 text-only literal Kling Omni prompt generation for any scene
(SC0047, SC0089, SC0111, ...).

For each scene: iterates all CLIP_*.yaml manifests under
  planning/scenes/<SCENE_ID>/manifests/
and calls KlingOmniAdapter.generate_from_clip_manifest() with
  language_profile=kling_literal_alias_locked, input_mode=text_only.

Also upserts rows into prompts/prompt_library.yaml and
evidence/scene_prompt_map.csv (idempotent).

Usage:
    python scripts/generate_v07_text_only.py --scene-ids SC0047,SC0089,SC0111 [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.agents.adapters.kling_omni import KlingOmniAdapter

_LANGUAGE_PROFILE = "kling_literal_alias_locked"
_VERSION = 7
_PROMPT_ID_BODY = re.compile(
    r"^(?P<scene_id>SC\d{4})__omni-kling-omni-clip-(?P<clip_slug>[a-z0-9\-]+)-safe__v\d+$"
)


def _write_yaml(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    content = yaml.dump(data, allow_unicode=True, sort_keys=False, width=120)
    if dry_run:
        print(f"# [dry-run] {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _v07_prompt_id(scene_id: str, clip_index: int) -> str:
    """Build the standard v07 prompt_id for clip N in scene."""
    slug = f"{scene_id.lower()}-{clip_index:02d}"
    return f"{scene_id}__omni-kling-omni-clip-clip-{slug}-safe__v{_VERSION:02d}"


def _generate_scene_records(
    scene_id: str,
    repo_root: Path,
    dry_run: bool,
    run_counter_start: int = 1,
) -> list[dict[str, Any]]:
    draft_dir = repo_root / "prompts" / "draft"
    runs_dir = repo_root / "evidence" / "prompt_runs"
    adapter = KlingOmniAdapter(repo_root=repo_root, model_guidance_mode="dynamic_snapshot")
    manifests_dir = repo_root / "planning" / "scenes" / scene_id / "manifests"
    manifest_paths = sorted(manifests_dir.glob("CLIP_*.yaml"))

    if not manifest_paths:
        print(f"  WARNING: no CLIP_*.yaml found in {manifests_dir}")
        return []

    records: list[dict[str, Any]] = []
    print(f"\n=== Generating v07 text_only literal Kling prompts for {scene_id} ({len(manifest_paths)} clips) ===")
    for idx, manifest_path in enumerate(manifest_paths, start=1):
        result = adapter.generate_from_clip_manifest(
            manifest_path,
            version=_VERSION,
            run_counter=run_counter_start + idx - 1,
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


def _update_prompt_library(
    scene_id: str,
    clip_count: int,
    repo_root: Path,
    dry_run: bool,
) -> None:
    path = repo_root / "prompts" / "prompt_library.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    prompts: list[dict[str, Any]] = data.get("prompts") or []

    existing_ids = {row.get("prompt_id") for row in prompts}
    added = 0
    for i in range(1, clip_count + 1):
        pid = _v07_prompt_id(scene_id, i)
        if pid in existing_ids:
            continue
        prompts.append(
            {
                "prompt_id": pid,
                "scene_id": scene_id,
                "prompt_type": "omni_instruction",
                "lifecycle_stage": "draft",
                "target_models": ["kling_omni"],
            }
        )
        added += 1

    data["prompts"] = prompts
    if not dry_run:
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
    print(f"  prompt_library.yaml: {added} new v07 row(s) upserted for {scene_id}")


def _update_scene_prompt_map(
    scene_id: str,
    clip_count: int,
    repo_root: Path,
    dry_run: bool,
) -> None:
    path = repo_root / "evidence" / "scene_prompt_map.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    existing_ids = {row.get("prompt_id") for row in rows}
    added = 0
    for i in range(1, clip_count + 1):
        pid = _v07_prompt_id(scene_id, i)
        if pid in existing_ids:
            continue
        rows.append(
            {
                "scene_id": scene_id,
                "prompt_id": pid,
                "prompt_type": "omni_instruction",
                "lifecycle_stage": "draft",
                "target_model": "kling_omni",
                "asset_ref": "pending_generation",
                "article3_flag": "",
                "notes": f"v07 text-only literal kling_literal_alias_locked prompt for CLIP_{scene_id}_{i:02d}",
            }
        )
        added += 1

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    if not dry_run:
        path.write_text(buf.getvalue(), encoding="utf-8", newline="")
    print(f"  scene_prompt_map.csv: {added} new v07 row(s) upserted for {scene_id}")


def generate(
    scene_ids: list[str],
    repo_root: Path,
    dry_run: bool = False,
) -> None:
    run_counter = 1
    for scene_id in scene_ids:
        manifests_dir = repo_root / "planning" / "scenes" / scene_id / "manifests"
        clip_count = len(list(manifests_dir.glob("CLIP_*.yaml")))
        records = _generate_scene_records(
            scene_id, repo_root, dry_run, run_counter_start=run_counter
        )
        run_counter += len(records)
        _update_prompt_library(scene_id, clip_count, repo_root, dry_run)
        _update_scene_prompt_map(scene_id, clip_count, repo_root, dry_run)
        print(f"  Total v07 records for {scene_id}: {len(records)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate v07 text-only literal Kling Omni prompts for one or more scenes."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument(
        "--scene-ids",
        required=True,
        help="Comma-separated scene IDs, e.g. SC0047,SC0089,SC0111",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print without writing files")
    args = parser.parse_args()
    scene_ids = [s.strip() for s in args.scene_ids.split(",") if s.strip()]
    generate(
        scene_ids=scene_ids,
        repo_root=Path(args.repo_root).resolve(),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
