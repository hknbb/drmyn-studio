"""Stage A closure placeholder audit.

Scans live repo files for remaining REPLACE_ME strings.
Excludes: evidence/provenance/**, .git/**, and other archival bundles.
Outputs JSON and Markdown reports to evidence/validation_reports/.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

REPORT_JSON = Path("evidence/validation_reports/stage_a_closure_placeholder_audit.json")
REPORT_MD = Path("evidence/validation_reports/stage_a_closure_placeholder_audit.md")

# Scan content file types only; exclude code/tooling files (.py, .sh, .toml)
# where the literal token appears as a search pattern, not as placeholder content.
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".csv", ".fountain", ".cfg"}

ARCHIVAL_PREFIXES = (
    "evidence/provenance/",
    ".git/",
)

GENERATED_REFRESHABLE_PREFIXES = (
    "evidence/validation_reports/",
    "evidence/article3/pilot_scene_review_packets/",
    "planning/manifests/",
    "source/screenplay/closing_price.numbered.fountain",
)

LIVE_FOUNDATION_PREFIXES = (
    "planning/continuity/",
    "planning/characters/",
    "planning/locations/",
    "planning/props/",
    "planning/wardrobe/",
    "planning/scenes/",
    "visual_dev/motion_prep/",
    "visual_dev/stills/",
    "visual_dev/characters/",
    "visual_dev/locations/",
    "source/story_blueprint.md",
    "source/character_dossier.md",
    "source/project_config.json",
    "source/style_bible.md",
    "source/continuity_bible.md",
    "source/location_bible.md",
    "source/screenplay/closing_price.fountain",
    "docs/",
    "schemas/",
    "prompts/",
    "scripts/",
)


def is_archival(rel: str) -> bool:
    return any(rel.startswith(p) for p in ARCHIVAL_PREFIXES)


def is_generated_refreshable(rel: str) -> bool:
    return any(rel.startswith(p) or rel == p for p in GENERATED_REFRESHABLE_PREFIXES)


def classify(rel: str) -> str:
    if is_archival(rel):
        return "archival_ignored"
    if is_generated_refreshable(rel):
        return "generated_refreshable"
    return "live"


def count_replace_me(path: Path) -> tuple[int, list[int]]:
    lines_found: list[int] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0, []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "REPLACE_ME" in line:
            lines_found.append(lineno)
    return len(lines_found), lines_found


def scan(root: Path) -> dict:
    live: list[dict] = []
    archival: list[dict] = []
    refreshable: list[dict] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".pre-commit-config.yaml"}:
            continue
        rel = path.relative_to(root).as_posix()
        category = classify(rel)
        count, lines = count_replace_me(path)
        if count == 0 and category == "live":
            continue
        entry = {
            "file": rel,
            "replace_me_count": count,
            "lines": lines,
        }
        if category == "archival_ignored":
            archival.append(entry)
        elif category == "generated_refreshable":
            if count > 0:
                refreshable.append(entry)
        else:
            if count > 0:
                live.append(entry)

    live.sort(key=lambda e: (-e["replace_me_count"], e["file"]))
    archival.sort(key=lambda e: (-e["replace_me_count"], e["file"]))
    refreshable.sort(key=lambda e: (-e["replace_me_count"], e["file"]))

    live_total = sum(e["replace_me_count"] for e in live)
    archival_total = sum(e["replace_me_count"] for e in archival)
    refreshable_total = sum(e["replace_me_count"] for e in refreshable)

    return {
        "date": str(date.today()),
        "summary": {
            "live_blocker_files": len(live),
            "live_blocker_replace_me_total": live_total,
            "archival_ignored_files": len(archival),
            "archival_ignored_replace_me_total": archival_total,
            "generated_refreshable_files": len(refreshable),
            "generated_refreshable_replace_me_total": refreshable_total,
        },
        "live_blockers": live,
        "generated_refreshable": refreshable,
        "archival_ignored": archival,
    }


def render_md(data: dict) -> str:
    s = data["summary"]
    lines = [
        "# Stage A Closure — Placeholder Audit",
        "",
        f"Date: `{data['date']}`",
        "",
        "## Summary",
        "",
        f"| Category | Files | REPLACE_ME count |",
        f"|----------|-------|-----------------|",
        f"| Live blockers | {s['live_blocker_files']} | {s['live_blocker_replace_me_total']} |",
        f"| Generated / refreshable | {s['generated_refreshable_files']} | {s['generated_refreshable_replace_me_total']} |",
        f"| Archival ignored | {s['archival_ignored_files']} | {s['archival_ignored_replace_me_total']} |",
        "",
        "## Live Blockers",
        "",
        "> Files in the live repo foundation that still contain REPLACE_ME strings.",
        "> These must reach zero before the canon-z1p1-r1 tag.",
        "",
    ]
    if not data["live_blockers"]:
        lines.append("**No live blockers detected. Stage A closure condition met.**")
    else:
        for entry in data["live_blockers"]:
            lines.append(f"### `{entry['file']}`")
            lines.append(f"- REPLACE_ME count: `{entry['replace_me_count']}`")
            lines.append(f"- Lines: {', '.join(str(ln) for ln in entry['lines'])}")
            lines.append("")

    lines += [
        "## Generated / Refreshable",
        "",
        "> These files are auto-generated. Remaining REPLACE_ME strings should be",
        "> resolved by re-running the relevant generator script, not hand-edited.",
        "",
    ]
    if not data["generated_refreshable"]:
        lines.append("No generated-refreshable files with REPLACE_ME detected.")
    else:
        for entry in data["generated_refreshable"]:
            lines.append(f"- `{entry['file']}` — {entry['replace_me_count']} occurrence(s) on lines {entry['lines']}")

    lines += [
        "",
        "## Archival Ignored",
        "",
        "> These files are in `evidence/provenance/` or other frozen archival bundles.",
        "> They are intentionally excluded from live closure scoring.",
        "",
    ]
    if not data["archival_ignored"]:
        lines.append("No archival files scanned (all excluded by prefix).")
    else:
        lines.append(
            f"Archival bundle files are excluded from scoring. "
            f"{s['archival_ignored_files']} files with REPLACE_ME in archival paths "
            f"({s['archival_ignored_replace_me_total']} total occurrences) are not counted as blockers."
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage A closure placeholder audit.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--report-json", default=str(REPORT_JSON))
    parser.add_argument("--report-md", default=str(REPORT_MD))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    data = scan(root)

    json_out = root / args.report_json
    md_out = root / args.report_md
    json_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    md_out.write_text(render_md(data), encoding="utf-8")

    s = data["summary"]
    print(
        f"Stage A closure audit complete. "
        f"Live blockers: {s['live_blocker_files']} files / {s['live_blocker_replace_me_total']} occurrences. "
        f"Archival ignored: {s['archival_ignored_files']} files."
    )
    return 0 if s["live_blocker_replace_me_total"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
