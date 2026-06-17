"""
generate_sc0014_v06_anchored.py

Faz 5 generation script: SC0014 v06 Anchor & Animate anchored package.

Writes to prompts/draft/:
  - 22 still_generation prompts (SC0014__still-01__v01.yaml … SC0014__still-22__v01.yaml)
  - 8 shot_design contact-sheet prompts (SC0014__contact-clip-01__v01.yaml … -08__v01.yaml)
  - 8 omni_instruction anchored_i2v Kling prompts

Writes run records to evidence/prompt_runs/.

Usage:
    python scripts/generate_sc0014_v06_anchored.py [--repo-root .] [--dry-run]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from scripts.agents.contact_sheet_planner import ContactSheetPlanner
from scripts.agents.shot_still_planner import ShotStillPlanner
from scripts.agents.shot_still_resolver import ShotStillResolver
from scripts.agents.adapters.kling_omni import KlingOmniAdapter

_SCENE_ID = "SC0014"
_PROJECT = "nexuszero"
_SHOTS_SUBDIR = "shots"


def _build_start_frame_refs(repo_root: Path) -> dict[str, str]:
    """Build start_frame_ref per clip_id using the resolver.

    pass-1 convention:
      - CLIP01: uses its own first shot (no predecessor)
      - CLIPn (n>1): uses last shot of CLIPn-1
    """
    resolver = ShotStillResolver(repo_root=repo_root, scene_id=_SCENE_ID)
    entries = resolver.resolve()

    # Group by clip_id preserving order
    clip_order: list[str] = []
    clip_entries: dict[str, list] = {}
    for e in entries:
        if e.clip_id not in clip_entries:
            clip_order.append(e.clip_id)
            clip_entries[e.clip_id] = []
        clip_entries[e.clip_id].append(e)

    prefix = f"archive/{_PROJECT}/{_SCENE_ID}/{_SHOTS_SUBDIR}"

    start_frame_refs: dict[str, str] = {}
    prev_last_fn: str | None = None
    for clip_id in clip_order:
        shots = clip_entries[clip_id]
        first_fn = shots[0].archive_filename
        last_fn = shots[-1].archive_filename

        if prev_last_fn is None:
            # First clip: use its own first shot as start frame
            start_frame_refs[clip_id] = f"{prefix}/{first_fn}"
        else:
            # Subsequent clip: use previous clip's last shot
            start_frame_refs[clip_id] = f"{prefix}/{prev_last_fn}"

        prev_last_fn = last_fn

    return start_frame_refs


def _write_yaml(path: Path, data: dict[str, Any], dry_run: bool) -> None:
    content = yaml.dump(data, allow_unicode=True, sort_keys=False, width=120)
    if dry_run:
        print(f"# [dry-run] {path}")
        print(content)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Written: {path.relative_to(path.parent.parent.parent)}")


def generate(repo_root: Path, dry_run: bool = False) -> None:
    draft_dir = repo_root / "prompts" / "draft"
    runs_dir = repo_root / "evidence" / "prompt_runs"

    # ----------------------------------------------------------------
    # 1. Shot still prompts (22)
    # ----------------------------------------------------------------
    print("\n=== Generating 22 still prompts ===")
    still_planner = ShotStillPlanner(repo_root=repo_root, scene_id=_SCENE_ID)
    still_records = still_planner.plan()
    for record in still_records:
        prompt_id: str = record["prompt_id"]
        _write_yaml(draft_dir / f"{prompt_id}.yaml", record, dry_run)
    print(f"Still prompts: {len(still_records)}")

    # ----------------------------------------------------------------
    # 2. Contact sheet prompts (8)
    # ----------------------------------------------------------------
    print("\n=== Generating 8 contact-sheet prompts ===")
    cs_planner = ContactSheetPlanner(repo_root=repo_root, scene_id=_SCENE_ID)
    cs_records = cs_planner.plan()
    for record in cs_records:
        prompt_id = record["prompt_id"]
        _write_yaml(draft_dir / f"{prompt_id}.yaml", record, dry_run)
    print(f"Contact-sheet prompts: {len(cs_records)}")

    # ----------------------------------------------------------------
    # 3. Anchored Kling prompts (8)
    # ----------------------------------------------------------------
    print("\n=== Generating 8 anchored_i2v Kling prompts ===")
    start_frame_refs = _build_start_frame_refs(repo_root)

    adapter = KlingOmniAdapter(repo_root=repo_root, model_guidance_mode="dynamic_snapshot")
    manifests_dir = repo_root / "planning" / "scenes" / _SCENE_ID / "manifests"
    manifest_paths = sorted(manifests_dir.glob("CLIP_*.yaml"))

    kling_count = 0
    for manifest_path in manifest_paths:
        import yaml as _y
        manifest_data = _y.safe_load(manifest_path.read_text(encoding="utf-8"))
        clip_id: str = manifest_data["clip_id"]
        start_frame_ref = start_frame_refs.get(clip_id)
        if not start_frame_ref:
            print(f"  WARNING: no start_frame_ref for {clip_id}, skipping")
            continue

        result = adapter.generate_from_clip_manifest(
            manifest_path,
            input_mode="anchored_i2v",
            start_frame_ref=start_frame_ref,
            variant_mode="safe",
            render_pass="visual_test",
            quality_tier="test_720p",
        )

        prompt_id = result.prompt_record["prompt_id"]
        _write_yaml(draft_dir / f"{prompt_id}.yaml", result.prompt_record, dry_run)
        _write_yaml(runs_dir / f"{result.run_record['run_id']}.yaml", result.run_record, dry_run)

        if result.warnings:
            for w in result.warnings:
                print(f"  WARNING [{clip_id}]: {w}")
        kling_count += 1

    print(f"Anchored Kling prompts: {kling_count}")
    print(f"\nTotal: {len(still_records) + len(cs_records) + kling_count} prompt records written.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SC0014 v06 anchored prompt package.")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without writing")
    args = parser.parse_args()
    generate(repo_root=Path(args.repo_root).resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
