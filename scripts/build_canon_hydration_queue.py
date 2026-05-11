from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


SCAN_ROOTS = ["source", "planning", "visual_dev", "prompts", "docs"]
SUPPORTED_TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".csv", ".fountain"}
PILOT_SCENES = {"SC0001", "SC0003", "SC0006", "SC0008", "SC0009"}
QUEUE_OUTPUT_JSON = Path("evidence/validation_reports/canon_hydration_queue.json")
QUEUE_OUTPUT_MD = Path("evidence/validation_reports/canon_hydration_queue.md")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        docs = list(yaml.safe_load_all(handle))
    if not docs:
        return None
    if len(docs) == 1:
        return docs[0]
    return docs


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_scene_card_path(path_str: str) -> bool:
    parts = path_str.split("/")
    return len(parts) >= 4 and parts[0] == "planning" and parts[1] == "scenes" and parts[-1] == "scene_card.yaml"


def rel_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def scan_text_placeholders(path: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        lowered = line.lower()
        if "no tbd" in lowered or "no placeholders" in lowered:
            continue
        if "REPLACE_ME" in line or "TBD" in line:
            findings.append(f"line {line_number}")
    return len(findings), findings


def scan_yaml_incomplete_fields(path: Path) -> tuple[int, list[str]]:
    data = load_yaml(path)
    findings: list[str] = []

    def walk(value: Any, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key in sorted(value.keys()):
                next_prefix = f"{prefix}.{key}" if prefix else key
                walk(value[key], next_prefix)
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{prefix}[{index}]")
            return
        if isinstance(value, str):
            stripped = value.strip()
            if "REPLACE_ME" in stripped or stripped.startswith("TBD"):
                findings.append(prefix)
            elif prefix == "status" and stripped == "scaffolded":
                findings.append(prefix)
            elif prefix == "review_status" and stripped == "needs_human_review":
                findings.append(prefix)
            return
        if value is None and prefix in {"location_text_raw", "time_of_day_text_raw"}:
            findings.append(prefix)

    walk(data)
    deduped = sorted(dict.fromkeys(findings))
    return len(deduped), deduped


def detect_machine_filled(path: Path, path_str: str) -> str:
    if "/manifests/" in path_str:
        return "machine-filled"
    if "/planning/scenes/" in f"/{path_str}" and path.name in {"scene_card.yaml", "prompt_brief.md", "review_notes.md"}:
        return "machine-filled"
    if "/visual_dev/" in path_str and path.name in {"notes.md", "selection_notes.md", "motion_notes.md"}:
        return "machine-filled"
    return "human-authored"


def detect_record_type(path: Path, path_str: str) -> str:
    if path_str.startswith("source/"):
        if path.name.endswith("_bible.md") or path.name in {"character_dossier.md", "story_blueprint.md"}:
            return "canonical_source_bible"
        if path.suffix == ".fountain":
            return "screenplay_source"
        return "source_record"
    if path_str.startswith("planning/characters/"):
        return "character_record"
    if path_str.startswith("planning/locations/"):
        return "location_record"
    if path_str.startswith("planning/props/"):
        return "prop_record"
    if path_str.startswith("planning/wardrobe/"):
        return "wardrobe_record"
    if path_str.startswith("planning/continuity/"):
        return "continuity_record"
    if is_scene_card_path(path_str):
        return "scene_card"
    if path_str.startswith("planning/scenes/") and path.name == "scene_excerpt.md":
        return "scene_excerpt"
    if path_str.startswith("planning/scenes/") and path.name == "review_notes.md":
        return "scene_review_notes"
    if path_str.startswith("planning/scenes/") and path.name == "prompt_brief.md":
        return "prompt_brief"
    if path_str.startswith("planning/manifests/"):
        return "generated_manifest"
    if path_str.startswith("visual_dev/characters/"):
        return "visual_character_notes"
    if path_str.startswith("visual_dev/locations/"):
        return "visual_location_notes"
    if path_str.startswith("visual_dev/motion_prep/"):
        return "motion_prep_notes"
    if path_str.startswith("visual_dev/stills/"):
        return "still_selection_notes"
    if path_str.startswith("prompts/"):
        return "prompt_governance_doc"
    if path_str.startswith("docs/"):
        return "documentation"
    return "text_record"


def queue_priority_for_path(path: Path, path_str: str) -> str | None:
    if path_str in {
        "source/story_blueprint.md",
        "source/character_dossier.md",
        "source/location_bible.md",
        "source/style_bible.md",
        "source/continuity_bible.md",
    }:
        return "A"
    if path_str.startswith("planning/characters/C") or path_str.startswith("planning/locations/") or path_str.startswith("planning/props/") or path_str.startswith("planning/wardrobe/"):
        return "B"
    if is_scene_card_path(path_str):
        scene_id = path_str.split("/")[2]
        return "C" if scene_id in PILOT_SCENES else "D"
    return None


def safe_for_automatic_fill(path: Path, path_str: str) -> bool:
    return detect_record_type(path, path_str) == "generated_manifest"


def dependencies_for_path(path: Path, path_str: str) -> list[str]:
    if path_str.startswith("source/"):
        return [
            "source/screenplay/closing_price.fountain",
            "planning/manifests/closing_price_scene_retrieval_map.json",
        ]
    if path_str.startswith("planning/characters/"):
        return [
            "source/character_dossier.md",
            "source/story_blueprint.md",
            "source/screenplay/closing_price.fountain",
        ]
    if path_str.startswith("planning/locations/"):
        return [
            "source/location_bible.md",
            "source/story_blueprint.md",
            "source/screenplay/closing_price.fountain",
        ]
    if path_str.startswith("planning/props/") or path_str.startswith("planning/wardrobe/"):
        return [
            "source/continuity_bible.md",
            "source/story_blueprint.md",
            "source/screenplay/closing_price.fountain",
        ]
    if is_scene_card_path(path_str):
        scene_id = path_str.split("/")[2]
        return [
            f"planning/scenes/{scene_id}/scene_excerpt.md",
            f"planning/scenes/{scene_id}/prompt_brief.md",
            "planning/manifests/closing_price_scene_retrieval_map.json",
            "source/screenplay/closing_price.numbered.fountain",
        ]
    if path_str.startswith("planning/manifests/"):
        return ["planning/", "scripts/build_manifests.py"]
    if path_str.startswith("visual_dev/"):
        return ["Priority A-C canon records", "planning/scenes/", "source/"]
    if path_str.startswith("prompts/") or path_str.startswith("docs/"):
        return ["Priority A-C canon records"]
    if path_str.startswith("planning/continuity/"):
        return ["source/continuity_bible.md", "planning/scenes/"]
    return []


def recommended_next_action(path: Path, path_str: str) -> str:
    record_type = detect_record_type(path, path_str)
    if record_type == "canonical_source_bible":
        return "Replace scaffold placeholders with reviewed canonical prose grounded in the screenplay."
    if record_type in {"character_record", "location_record", "prop_record", "wardrobe_record"}:
        return "Fill placeholder fields from canonical bibles and screenplay evidence; do not guess."
    if record_type == "scene_card":
        return "Use the pilot packet or scene excerpt to replace remaining scaffold fields and confirm hydrated metadata."
    if record_type == "generated_manifest":
        return "Do not edit directly; rebuild after upstream records are completed."
    if record_type in {"motion_prep_notes", "still_selection_notes", "visual_character_notes", "visual_location_notes"}:
        return "Hold downstream visual notes until canon hydration is complete, then replace scaffold placeholders."
    if record_type in {"prompt_governance_doc", "documentation", "scene_review_notes", "prompt_brief", "continuity_record"}:
        return "Review the scaffold content manually and replace placeholders only after upstream canon is stable."
    return "Review manually before editing."


def review_notes_for_path(path: Path, path_str: str, findings: list[str]) -> list[str]:
    notes: list[str] = []
    record_type = detect_record_type(path, path_str)
    priority = queue_priority_for_path(path, path_str)
    if priority == "A":
        notes.append("Canonical bible content should be reviewed before any downstream planning record is finalized.")
    if priority == "B":
        notes.append("Core planning records should not be normalized further until Priority A bibles are stable.")
    if priority == "C":
        notes.append("Pilot scenes are the first human-review tranche for canon hydration.")
    if priority == "D":
        notes.append("Remaining scenes should follow the conventions established in Priority C reviews.")
    if is_scene_card_path(path_str):
        notes.append("Hydrated metadata is machine-generated and should only be adjusted for consistency with the excerpt.")
    if record_type == "generated_manifest":
        notes.append("Manifest placeholders are derived from upstream records and should be regenerated, not hand-edited.")
    if any(field in {"location_text_raw", "time_of_day_text_raw"} for field in findings):
        notes.append("Null raw anchors may be legitimate for dash-start scenes; review against the excerpt before filling.")
    if not notes:
        notes.append("Human review required before canonical completion.")
    return notes


def build_entry(path: Path, root: Path) -> dict[str, Any]:
    path_str = rel_path(path, root)
    if path.suffix in {".yaml", ".yml"}:
        placeholder_count, placeholder_refs = scan_yaml_incomplete_fields(path)
    else:
        placeholder_count, placeholder_refs = scan_text_placeholders(path)

    return {
        "dependencies": dependencies_for_path(path, path_str),
        "file_path": path_str,
        "machine_filled_or_human_authored": detect_machine_filled(path, path_str),
        "placeholder_count": placeholder_count,
        "placeholder_lines_or_fields": placeholder_refs,
        "priority_bucket": queue_priority_for_path(path, path_str),
        "record_type": detect_record_type(path, path_str),
        "recommended_next_action": recommended_next_action(path, path_str),
        "review_notes": review_notes_for_path(path, path_str, placeholder_refs),
        "safe_for_automatic_fill": safe_for_automatic_fill(path, path_str),
    }


def queue_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    targets.extend(
        [
            root / "source/story_blueprint.md",
            root / "source/character_dossier.md",
            root / "source/location_bible.md",
            root / "source/style_bible.md",
            root / "source/continuity_bible.md",
        ]
    )
    targets.extend(sorted((root / "planning/characters").glob("C0*.yaml")))
    targets.extend(sorted((root / "planning/locations").glob("*.yaml")))
    targets.extend(sorted((root / "planning/props").glob("*.yaml")))
    targets.extend(sorted((root / "planning/wardrobe").glob("*.yaml")))
    targets.extend(sorted((root / "planning/scenes").glob("SC*/scene_card.yaml")))
    return targets


def supplemental_scan(root: Path, target_paths: set[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_TEXT_SUFFIXES):
            relative = rel_path(path, root)
            if relative in target_paths:
                continue
            entry = build_entry(path, root)
            if entry["record_type"] in {"screenplay_source", "scene_excerpt"}:
                continue
            if entry["placeholder_count"] > 0:
                findings.append(entry)
    return findings


def bucketed_queue(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {"A": [], "B": [], "C": [], "D": []}
    for entry in entries:
        bucket = entry["priority_bucket"]
        if bucket in buckets:
            buckets[bucket].append(entry)
    for bucket in buckets:
        buckets[bucket] = sorted(buckets[bucket], key=lambda item: (-item["placeholder_count"], item["file_path"]))
    return buckets


def summary(queue_by_bucket: dict[str, list[dict[str, Any]]], supplemental: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_summary: dict[str, dict[str, int]] = {}
    for bucket, entries in queue_by_bucket.items():
        bucket_summary[bucket] = {
            "files": len(entries),
            "placeholder_total": sum(entry["placeholder_count"] for entry in entries),
        }
    return {
        "priority_buckets": bucket_summary,
        "supplemental_findings": {
            "files": len(supplemental),
            "placeholder_total": sum(entry["placeholder_count"] for entry in supplemental),
        },
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Canon Hydration Queue",
        "",
        "This report lists canonical hydration work that still requires human review.",
        "",
        "## Summary",
        "",
    ]
    for bucket in ["A", "B", "C", "D"]:
        summary_row = payload["summary"]["priority_buckets"][bucket]
        lines.append(
            f"- Priority {bucket}: {summary_row['files']} files, {summary_row['placeholder_total']} placeholder or scaffold findings"
        )
    supplemental_summary = payload["summary"]["supplemental_findings"]
    lines.append(
        f"- Supplemental findings: {supplemental_summary['files']} files, {supplemental_summary['placeholder_total']} findings"
    )

    for bucket in ["A", "B", "C", "D"]:
        lines.extend(["", f"## Priority {bucket}", ""])
        for entry in payload["queue"][bucket]:
            lines.extend(
                [
                    f"### `{entry['file_path']}`",
                    "",
                    f"- Record type: `{entry['record_type']}`",
                    f"- Placeholder count: `{entry['placeholder_count']}`",
                    f"- Machine-filled or human-authored: `{entry['machine_filled_or_human_authored']}`",
                    f"- Safe for automatic fill: `{str(entry['safe_for_automatic_fill']).lower()}`",
                    f"- Recommended next action: {entry['recommended_next_action']}",
                    f"- Dependencies: {', '.join(f'`{item}`' for item in entry['dependencies']) if entry['dependencies'] else '_None_'}",
                    f"- Placeholder lines or fields: {', '.join(f'`{item}`' for item in entry['placeholder_lines_or_fields']) if entry['placeholder_lines_or_fields'] else '_None_'}",
                    f"- Review notes: {' '.join(entry['review_notes'])}",
                    "",
                ]
            )

    lines.extend(["## Supplemental Findings", ""])
    if not payload["supplemental_findings"]:
        lines.append("No supplemental findings detected.")
    else:
        for entry in payload["supplemental_findings"]:
            lines.extend(
                [
                    f"### `{entry['file_path']}`",
                    "",
                    f"- Record type: `{entry['record_type']}`",
                    f"- Placeholder count: `{entry['placeholder_count']}`",
                    f"- Machine-filled or human-authored: `{entry['machine_filled_or_human_authored']}`",
                    f"- Safe for automatic fill: `{str(entry['safe_for_automatic_fill']).lower()}`",
                    f"- Recommended next action: {entry['recommended_next_action']}",
                    f"- Dependencies: {', '.join(f'`{item}`' for item in entry['dependencies']) if entry['dependencies'] else '_None_'}",
                    f"- Placeholder lines or fields: {', '.join(f'`{item}`' for item in entry['placeholder_lines_or_fields']) if entry['placeholder_lines_or_fields'] else '_None_'}",
                    f"- Review notes: {' '.join(entry['review_notes'])}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def build_queue(root: Path, report_json: Path, report_md: Path) -> int:
    targets = queue_targets(root)
    queue_entries = [build_entry(path, root) for path in targets if path.exists()]
    queue_by_bucket = bucketed_queue(queue_entries)

    target_paths = {entry["file_path"] for entry in queue_entries}
    supplemental = supplemental_scan(root, target_paths)
    supplemental = sorted(supplemental, key=lambda item: (-item["placeholder_count"], item["file_path"]))

    payload = {
        "queue": queue_by_bucket,
        "scan_roots": SCAN_ROOTS,
        "summary": summary(queue_by_bucket, supplemental),
        "supplemental_findings": supplemental,
    }

    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    report_md.write_text(render_markdown_report(payload), encoding="utf-8")

    print(
        "Canon hydration queue built:",
        f"A={len(queue_by_bucket['A'])},",
        f"B={len(queue_by_bucket['B'])},",
        f"C={len(queue_by_bucket['C'])},",
        f"D={len(queue_by_bucket['D'])},",
        f"supplemental={len(supplemental)}",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--report-json", default=str(QUEUE_OUTPUT_JSON))
    parser.add_argument("--report-md", default=str(QUEUE_OUTPUT_MD))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return build_queue(root, root / args.report_json, root / args.report_md)


if __name__ == "__main__":
    raise SystemExit(main())
