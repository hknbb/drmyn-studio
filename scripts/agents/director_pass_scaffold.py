"""
Director-pass scaffold generator (P3).

omni_clip_planner is a deterministic duration packer; the "director pass" that
adds coverage, per-shot entry_state/exit_state, and per-figure actions is fully
manual (see omni_clip_planner.py's own note that coverage "is authored at the
manifest level by the director pass, not fabricated here"). Authoring those
state stubs by hand for every shot is slow and is exactly where the ledger ↔
manifest drift (P4) creeps in.

This generator does NOT invent blocking. It restructures what is already
authored: it carries the *settled* state forward — the clip's ledger entry_state
into the first shot, then each shot's exit_state into the next shot's entry_state
— and drops a TODO ``action`` stub on every figure that lacks one. Positions are
copied, never fabricated, so the scaffold and the ledger start consistent (which
is what the P4 consistency validator checks). Every stub is marked TODO for the
human director pass to refine.

Output is a DRAFT written to a ``*.scaffold.yaml`` path; it never overwrites the
authored manifest.

Usage:
    python scripts/agents/director_pass_scaffold.py --scene SC0014 --clip CLIP_SC0014_03
    python scripts/agents/director_pass_scaffold.py --scene SC0014 --clip CLIP_SC0014_03 --write
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

_TODO_SUMMARY = "TODO(scaffold): author the settled state for this shot."
_TODO_ACTION = "TODO(scaffold): author this figure's action."


def _carry_state(source: dict | None, summary_todo: bool) -> dict:
    """Copy a settled state forward, keeping positions/props, resetting summary."""
    carried: dict = {}
    if isinstance(source, dict):
        for key in ("key_positions", "props_state", "camera_state", "screen_direction"):
            if key in source:
                carried[key] = copy.deepcopy(source[key])
    if summary_todo or "summary" not in carried:
        carried["summary"] = _TODO_SUMMARY
    return carried


def scaffold_director_pass(
    manifest: dict,
    ledger_entry_state: dict | None,
    ledger_exit_state: dict | None,
) -> dict:
    """Return a copy of *manifest* with draft entry/exit_state + figure-action stubs.

    Existing authored values are preserved; only missing fields are stubbed.
    """
    out = copy.deepcopy(manifest)
    shots = out.get("shots") or []
    prev_exit: dict | None = ledger_exit_state

    for idx, shot in enumerate(shots):
        if not isinstance(shot, dict):
            continue

        # entry_state: first shot ← ledger clip entry; later shots ← prior exit.
        if not isinstance(shot.get("entry_state"), dict):
            source = ledger_entry_state if idx == 0 else prev_exit
            shot["entry_state"] = _carry_state(source, summary_todo=False)

        # exit_state: carry this shot's entry forward as a starting point.
        if not isinstance(shot.get("exit_state"), dict):
            shot["exit_state"] = _carry_state(shot.get("entry_state"), summary_todo=True)
        prev_exit = shot["exit_state"]

        # figures[].action: stub any figure missing one.
        for fig in shot.get("figures") or []:
            if isinstance(fig, dict) and not (
                isinstance(fig.get("action"), str) and fig["action"].strip()
            ):
                alias = fig.get("kling_alias", fig.get("figure_id", "figure"))
                fig["action"] = f"{_TODO_ACTION} ({alias})"

    return out


def _load_yaml(path: Path):
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ledger_states_for_clip(ledger: dict | None, clip_id: str) -> tuple[dict | None, dict | None]:
    if not isinstance(ledger, dict):
        return None, None
    for entry in ledger.get("clip_chain") or []:
        if isinstance(entry, dict) and entry.get("clip_id") == clip_id:
            return entry.get("entry_state"), entry.get("exit_state")
    return None, None


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a draft director-pass manifest scaffold.")
    p.add_argument("--scene", required=True, help="Scene id, e.g. SC0014")
    p.add_argument("--clip", required=True, help="Clip id, e.g. CLIP_SC0014_03")
    p.add_argument("--repo-root", default=".", help="Repository root (default: .)")
    p.add_argument(
        "--write",
        action="store_true",
        help="Write the manifest's <name>.scaffold.yaml (never overwrites the authored manifest).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    manifests_dir = repo_root / "planning" / "scenes" / args.scene / "manifests"

    manifest_path = None
    for mpath in sorted(manifests_dir.glob("*.yaml")):
        doc = _load_yaml(mpath)
        if isinstance(doc, dict) and doc.get("clip_id") == args.clip:
            manifest_path, manifest = mpath, doc
            break
    if manifest_path is None:
        print(f"ERROR: no manifest for clip {args.clip} in {manifests_dir}", file=sys.stderr)
        return 1

    ledger = _load_yaml(
        repo_root / "planning" / "scenes" / args.scene / "scene_continuity_ledger.yaml"
    )
    led_entry, led_exit = _ledger_states_for_clip(ledger, args.clip)

    record = scaffold_director_pass(manifest, led_entry, led_exit)
    text = yaml.safe_dump(record, sort_keys=False, allow_unicode=True)

    if args.write:
        out = manifest_path.with_suffix(".scaffold.yaml")
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
