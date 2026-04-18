from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_scene_index(planning_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scenes_dir = planning_dir / "scenes"
    if not scenes_dir.exists():
        return rows
    for card_path in sorted(scenes_dir.glob("SC*/scene_card.yaml")):
        data = load_yaml(card_path)
        continuity_refs = data.get("continuity_refs", {})
        rows.append({
            "scene_id": data.get("scene_id", ""),
            "sequence_id": data.get("sequence_id", ""),
            "phase_id": data.get("phase_id", ""),
            "beat_id": data.get("beat_id", ""),
            "title": data.get("title", ""),
            "location_id": data.get("location_id", ""),
            "time_of_day": data.get("time_of_day", ""),
            "characters_present": "|".join(data.get("characters_present", [])),
            "wardrobe_refs": "|".join(continuity_refs.get("wardrobe", [])),
            "prop_refs": "|".join(continuity_refs.get("props", [])),
            "prior_scenes": "|".join(continuity_refs.get("prior_scenes", [])),
            "next_expected_links": "|".join(continuity_refs.get("next_expected_links", [])),
            "status": data.get("status", ""),
            "review_status": data.get("review_status", ""),
            "canon_lock": data.get("canon_lock", False),
        })
    return rows


def build_character_index(planning_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    chars_dir = planning_dir / "characters"
    if not chars_dir.exists():
        return rows
    for file_path in sorted(chars_dir.glob("*.yaml")):
        data = load_yaml(file_path)
        refs = data.get("continuity_refs", {})
        rows.append({
            "character_id": data.get("character_id", ""),
            "display_name": data.get("display_name", ""),
            "cue_name": data.get("cue_name", ""),
            "role": data.get("role", ""),
            "initial_arc_phase": data.get("arc_baseline", {}).get("initial_arc_phase", ""),
            "wardrobe_ids": "|".join(refs.get("wardrobe_ids", [])),
            "prop_ids": "|".join(refs.get("prop_ids", [])),
            "key_scene_ids": "|".join(refs.get("key_scene_ids", [])),
            "status": data.get("status", ""),
            "review_status": data.get("review_status", ""),
            "canon_lock": data.get("canon_lock", False),
        })
    return rows


def build_location_index(planning_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    locs_dir = planning_dir / "locations"
    if not locs_dir.exists():
        return rows
    for file_path in sorted(locs_dir.glob("*.yaml")):
        data = load_yaml(file_path)
        constraints = data.get("continuity_constraints", {})
        rows.append({
            "location_id": data.get("location_id", ""),
            "name": data.get("name", ""),
            "category": data.get("category", ""),
            "recurring": data.get("recurring", False),
            "persistent_objects": "|".join(constraints.get("persistent_objects", [])),
            "scene_refs": "|".join(data.get("scene_refs", [])),
            "status": data.get("status", ""),
            "review_status": data.get("review_status", ""),
            "canon_lock": data.get("canon_lock", False),
        })
    return rows


def build_continuity_index(planning_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for file_path in sorted((planning_dir / "wardrobe").glob("*.yaml")):
        data = load_yaml(file_path)
        rows.append({
            "record_type": "wardrobe",
            "record_id": data.get("wardrobe_id", ""),
            "label": data.get("name", ""),
            "scene_refs": "|".join(data.get("scene_refs", [])),
            "status": data.get("status", ""),
            "canon_lock": data.get("canon_lock", False),
        })

    for file_path in sorted((planning_dir / "props").glob("*.yaml")):
        data = load_yaml(file_path)
        rows.append({
            "record_type": "prop",
            "record_id": data.get("prop_id", ""),
            "label": data.get("name", ""),
            "scene_refs": "|".join(data.get("scene_refs", [])),
            "status": data.get("status", ""),
            "canon_lock": data.get("canon_lock", False),
        })

    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--planning-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    planning_dir = Path(args.planning_dir)
    output_dir = Path(args.output_dir)

    scene_rows = build_scene_index(planning_dir)
    character_rows = build_character_index(planning_dir)
    location_rows = build_location_index(planning_dir)
    continuity_rows = build_continuity_index(planning_dir)

    write_csv(output_dir / "scene_index.csv", [
        "scene_id", "sequence_id", "phase_id", "beat_id", "title",
        "location_id", "time_of_day", "characters_present",
        "wardrobe_refs", "prop_refs", "prior_scenes", "next_expected_links",
        "status", "review_status", "canon_lock",
    ], scene_rows)

    write_csv(output_dir / "character_index.csv", [
        "character_id", "display_name", "cue_name", "role", "initial_arc_phase",
        "wardrobe_ids", "prop_ids", "key_scene_ids",
        "status", "review_status", "canon_lock",
    ], character_rows)

    write_csv(output_dir / "location_index.csv", [
        "location_id", "name", "category", "recurring",
        "persistent_objects", "scene_refs",
        "status", "review_status", "canon_lock",
    ], location_rows)

    write_csv(output_dir / "continuity_index.csv", [
        "record_type", "record_id", "label", "scene_refs", "status", "canon_lock",
    ], continuity_rows)

    print(f"Manifests rebuilt: {len(scene_rows)} scenes, {len(character_rows)} characters, "
          f"{len(location_rows)} locations, {len(continuity_rows)} continuity records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
