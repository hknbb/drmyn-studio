from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml


@dataclass
class IntegrityIssue:
    level: str
    file: str
    message: str


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_ids_from_directory(path: Path, key: str) -> dict[str, Path]:
    records: dict[str, Path] = {}
    if not path.exists():
        return records
    for file_path in sorted(path.glob("*.yaml")):
        data = load_yaml(file_path)
        record_id = data.get(key)
        if isinstance(record_id, str):
            records[record_id] = file_path
    return records


def collect_scene_cards(scene_root: Path) -> dict[str, Path]:
    cards: dict[str, Path] = {}
    if not scene_root.exists():
        return cards
    for file_path in sorted(scene_root.glob("SC*/scene_card.yaml")):
        data = load_yaml(file_path)
        scene_id = data.get("scene_id")
        if isinstance(scene_id, str):
            cards[scene_id] = file_path
    return cards


def collect_prompt_records(prompts_root: Path) -> list[Path]:
    records: list[Path] = []
    if not prompts_root.exists():
        return records
    for stage_dir in ["draft", "review", "approved", "locked"]:
        d = prompts_root / stage_dir
        if not d.exists():
            continue
        records.extend(sorted(d.glob("*.yaml")))
    return records


def check_scene_card_references(
    scene_cards: dict[str, Path],
    character_records: dict[str, Path],
    location_records: dict[str, Path],
    wardrobe_records: dict[str, Path],
    prop_records: dict[str, Path],
) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    for scene_id, card_path in scene_cards.items():
        data = load_yaml(card_path)

        location_id = data.get("location_id")
        if location_id and location_id not in location_records:
            issues.append(IntegrityIssue(
                level="error",
                file=str(card_path),
                message=f"Missing referenced location record: {location_id}",
            ))

        for character_id in data.get("characters_present", []):
            if character_id not in character_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Missing referenced character record: {character_id}",
                ))

        continuity_refs = data.get("continuity_refs", {})

        for wardrobe_id in continuity_refs.get("wardrobe", []):
            if wardrobe_id not in wardrobe_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Missing referenced wardrobe record: {wardrobe_id}",
                ))

        for prop_id in continuity_refs.get("props", []):
            if prop_id not in prop_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Missing referenced prop record: {prop_id}",
                ))

        for prior_scene_id in continuity_refs.get("prior_scenes", []):
            if prior_scene_id not in scene_cards:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(card_path),
                    message=f"Missing referenced prior scene card: {prior_scene_id}",
                ))

        for next_scene_id in continuity_refs.get("next_expected_links", []):
            if next_scene_id not in scene_cards:
                issues.append(IntegrityIssue(
                    level="warning",
                    file=str(card_path),
                    message=f"Missing referenced next expected scene card: {next_scene_id}",
                ))

        for ref_name in ["screen_excerpt_ref", "prompt_brief_ref", "review_notes_ref"]:
            ref = data.get(ref_name)
            if ref and not (card_path.parent / ref).exists():
                issues.append(IntegrityIssue(
                    level="warning",
                    file=str(card_path),
                    message=f"Referenced companion file not found: {ref}",
                ))

    return issues


def check_character_record_references(
    character_records: dict[str, Path],
    wardrobe_records: dict[str, Path],
    prop_records: dict[str, Path],
    scene_cards: dict[str, Path],
) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    for character_id, file_path in character_records.items():
        data = load_yaml(file_path)
        refs = data.get("continuity_refs", {})

        for wardrobe_id in refs.get("wardrobe_ids", []):
            if wardrobe_id not in wardrobe_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Missing wardrobe reference: {wardrobe_id}",
                ))

        for prop_id in refs.get("prop_ids", []):
            if prop_id not in prop_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Missing prop reference: {prop_id}",
                ))

        for scene_id in refs.get("key_scene_ids", []):
            if scene_id not in scene_cards:
                issues.append(IntegrityIssue(
                    level="warning",
                    file=str(file_path),
                    message=f"Missing key scene reference: {scene_id}",
                ))

    return issues


def check_location_record_references(
    location_records: dict[str, Path],
    prop_records: dict[str, Path],
    scene_cards: dict[str, Path],
) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    for location_id, file_path in location_records.items():
        data = load_yaml(file_path)
        constraints = data.get("continuity_constraints", {})

        for prop_id in constraints.get("persistent_objects", []):
            if prop_id not in prop_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Missing persistent object reference: {prop_id}",
                ))

        for scene_id in data.get("scene_refs", []):
            if scene_id not in scene_cards:
                issues.append(IntegrityIssue(
                    level="warning",
                    file=str(file_path),
                    message=f"Missing scene reference: {scene_id}",
                ))

    return issues


def check_prompt_record_references(
    prompt_record_paths: list[Path],
    scene_cards: dict[str, Path],
    character_records: dict[str, Path],
    location_records: dict[str, Path],
    prop_records: dict[str, Path],
) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []

    for file_path in prompt_record_paths:
        data = load_yaml(file_path)

        scene_id = data.get("scene_id")
        if scene_id and scene_id not in scene_cards:
            issues.append(IntegrityIssue(
                level="error",
                file=str(file_path),
                message=f"Prompt record references missing scene_id: {scene_id}",
            ))

        source_refs = data.get("source_refs", {})

        for character_id in source_refs.get("character_refs", []):
            if character_id not in character_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Prompt record references missing character: {character_id}",
                ))

        for location_id in source_refs.get("location_refs", []):
            if location_id not in location_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Prompt record references missing location: {location_id}",
                ))

        for prop_id in source_refs.get("prop_refs", []):
            if prop_id not in prop_records:
                issues.append(IntegrityIssue(
                    level="error",
                    file=str(file_path),
                    message=f"Prompt record references missing prop: {prop_id}",
                ))

    return issues


def write_report(path: Path, issues: list[IntegrityIssue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": not any(i.level == "error" for i in issues),
        "issue_count": len(issues),
        "issues": [asdict(i) for i in issues],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--planning-dir", required=True)
    parser.add_argument("--prompts-dir", required=False, default="prompts")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    planning_dir = Path(args.planning_dir)
    prompts_dir = Path(args.prompts_dir)

    scene_cards = collect_scene_cards(planning_dir / "scenes")
    character_records = collect_ids_from_directory(planning_dir / "characters", "character_id")
    location_records = collect_ids_from_directory(planning_dir / "locations", "location_id")
    prop_records = collect_ids_from_directory(planning_dir / "props", "prop_id")
    wardrobe_records = collect_ids_from_directory(planning_dir / "wardrobe", "wardrobe_id")
    prompt_record_paths = collect_prompt_records(prompts_dir)

    issues: list[IntegrityIssue] = []
    issues.extend(check_scene_card_references(
        scene_cards=scene_cards,
        character_records=character_records,
        location_records=location_records,
        wardrobe_records=wardrobe_records,
        prop_records=prop_records,
    ))
    issues.extend(check_character_record_references(
        character_records=character_records,
        wardrobe_records=wardrobe_records,
        prop_records=prop_records,
        scene_cards=scene_cards,
    ))
    issues.extend(check_location_record_references(
        location_records=location_records,
        prop_records=prop_records,
        scene_cards=scene_cards,
    ))
    issues.extend(check_prompt_record_references(
        prompt_record_paths=prompt_record_paths,
        scene_cards=scene_cards,
        character_records=character_records,
        location_records=location_records,
        prop_records=prop_records,
    ))

    write_report(Path(args.output), issues)

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    print(f"Integrity check complete: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
