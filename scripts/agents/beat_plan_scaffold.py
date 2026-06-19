"""
Beat-plan scaffold generator (P1).

The screenplay → beat-plan step is the most creative and error-prone hand step
in the pipeline, and no script supports it: omni_clip_planner already consumes
beats as input. This generator does NOT author cinematic intent. It restructures
the already-authored scene_excerpt.md into a *skeleton* scene_beat_plan.yaml —
one beat per source paragraph, with ``content`` copied verbatim from the source
(no invented story facts) and every creative field (narrative_role, camera,
required_element_ids, figures, performance_note) left for the human to fill in.

Each beat carries only the schema-required fields plus a ``notes`` TODO marker.
The output is a DRAFT for human completion and PR review; it is written to a
``*.scaffold.yaml`` path and never overwrites an authored scene_beat_plan.yaml.

Usage:
    python scripts/agents/beat_plan_scaffold.py --scene SC0014           # dry-run to stdout
    python scripts/agents/beat_plan_scaffold.py --scene SC0014 --write   # write *.scaffold.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

_FENCE_RE = re.compile(r"```fountain\s*\n(.*?)```", re.DOTALL)
_CONTENT_MAX = 2000
_CUE_RE = re.compile(r"^[A-Z][A-Z0-9 .'\-]{1,30}(\(.*\))?$")


def extract_fountain(excerpt_text: str) -> str:
    """Return the fountain code block from a scene_excerpt.md, or '' if absent."""
    m = _FENCE_RE.search(excerpt_text)
    return m.group(1).strip() if m else ""


def split_units(fountain: str) -> list[str]:
    """Split the fountain text into blank-line-separated units, dropping the
    opening slugline (INT./EXT. …) which is not a beat."""
    raw = [u.strip() for u in re.split(r"\n\s*\n", fountain) if u.strip()]
    units: list[str] = []
    for u in raw:
        first = u.splitlines()[0].strip()
        if first.startswith(("INT.", "EXT.", "INT/EXT", "I/E")):
            continue
        units.append(re.sub(r"\s+", " ", u).strip())
    return units


def _is_dialogue_unit(unit: str) -> bool:
    """Heuristic: a unit whose first line is an all-caps character cue."""
    first = unit.split(".")[0].strip()
    return bool(_CUE_RE.match(first)) and first.upper() == first


def scaffold_beat_plan(scene_id: str, excerpt_text: str) -> dict:
    """Build a schema-valid skeleton scene_beat_plan record (draft)."""
    fountain = extract_fountain(excerpt_text)
    units = split_units(fountain)

    beats: list[dict] = []
    for idx, unit in enumerate(units, start=1):
        is_dialogue = _is_dialogue_unit(unit)
        beats.append(
            {
                "beat_id": f"BEAT_{idx:02d}",
                "content": unit[:_CONTENT_MAX],
                "semantic_duration_hint": "normal",
                "may_merge_with_next": False,
                "splittable": True,
                # Every creative field is intentionally omitted for the human to
                # author. The TODO records exactly what is still needed.
                "notes": (
                    "TODO(scaffold): set narrative_role"
                    + (", wire dialogue_line target_beat_id" if is_dialogue else "")
                    + ", required_element_ids, camera/lighting/motion, figures, "
                    "and coverage. Content copied verbatim from scene_excerpt.md "
                    "— do not treat as final phrasing."
                ),
            }
        )

    return {
        "schema_version": "0.x-draft",
        "record_type": "scene_beat_plan",
        "scene_id": scene_id,
        "notes": (
            f"SCAFFOLD for {scene_id} — auto-generated skeleton from "
            "scene_excerpt.md by beat_plan_scaffold.py. One beat per source unit; "
            "content verbatim, no story facts added. All creative fields are TODO "
            "and must be authored by a human before this is used as a real beat plan."
        ),
        "source_beats": beats,
        "provenance": {
            "created_by": "claude_code (beat_plan_scaffold P1)",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a draft scene_beat_plan scaffold.")
    p.add_argument("--scene", required=True, help="Scene id, e.g. SC0014")
    p.add_argument("--repo-root", default=".", help="Repository root (default: .)")
    p.add_argument(
        "--write",
        action="store_true",
        help="Write planning/scenes/<scene>/scene_beat_plan.scaffold.yaml "
        "(never overwrites an authored scene_beat_plan.yaml).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    excerpt_path = repo_root / "planning" / "scenes" / args.scene / "scene_excerpt.md"
    if not excerpt_path.exists():
        print(f"ERROR: missing {excerpt_path}", file=sys.stderr)
        return 1

    record = scaffold_beat_plan(args.scene, excerpt_path.read_text(encoding="utf-8"))
    text = yaml.safe_dump(record, sort_keys=False, allow_unicode=True)

    if not record["source_beats"]:
        print(f"ERROR: no fountain beats found in {excerpt_path}", file=sys.stderr)
        return 1

    if args.write:
        out = excerpt_path.parent / "scene_beat_plan.scaffold.yaml"
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out} ({len(record['source_beats'])} draft beats)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
