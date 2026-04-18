from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


PILOT_SCENES = ["SC0001", "SC0003", "SC0006", "SC0008", "SC0009"]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def extract_fountain_block(markdown_text: str) -> str:
    fence = "```fountain\n"
    start = markdown_text.index(fence) + len(fence)
    end = markdown_text.index("\n```", start)
    return markdown_text[start:end]


def render_yaml_block(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False, width=100).rstrip()


def missing_fields(scene_card: dict[str, Any]) -> list[str]:
    missing: list[str] = []

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
                missing.append(prefix)
            elif prefix == "status" and stripped == "scaffolded":
                missing.append(prefix)
            elif prefix == "review_status" and stripped == "needs_human_review":
                missing.append(prefix)
            return
        if value is None and prefix in {"location_text_raw", "time_of_day_text_raw"}:
            missing.append(prefix)

    walk(scene_card)
    return sorted(dict.fromkeys(missing))


def review_questions(scene_id: str, scene_card: dict[str, Any], missing: list[str]) -> list[str]:
    questions = [
        "Which `REPLACE_ME` fields can be completed directly from the source excerpt without interpretation?",
        "Which remaining fields depend on Priority A or Priority B canon records before they can be finalized?",
        "Do the raw characters detected here align with the canonical character IDs already referenced in the scene card?",
    ]

    if scene_card.get("mapping_confidence") != "high":
        questions.append("Does the inferred boundary need human confirmation before any canon prose is finalized?")
    if scene_card.get("location_text_raw") is None or scene_card.get("time_of_day_text_raw") is None:
        questions.append("Should raw location/time remain null because the scene opens on a dash boundary, or can they be anchored later in the excerpt without guessing?")
    if any(field.startswith("visual_targets.") for field in missing):
        questions.append("Should visual target placeholders remain untouched in this pass until canon hydration is complete?")
    if scene_id in {"SC0008", "SC0009"}:
        questions.append("If the excerpt splits between a dash-start beat and a later slugline, which portion belongs in the canonical scene summary and which should remain as a retrieval artifact note?")
    return questions


def build_packet(scene_dir: Path, output_path: Path) -> None:
    scene_id = scene_dir.name
    scene_card = load_yaml(scene_dir / "scene_card.yaml")
    excerpt_text = extract_fountain_block((scene_dir / "scene_excerpt.md").read_text(encoding="utf-8"))
    missing = missing_fields(scene_card)
    dialogue_chars = scene_card.get("characters_explicit_dialogue", [])
    mention_chars = scene_card.get("characters_explicit_mentions", [])
    location_text = scene_card.get("location_text_raw")
    time_text = scene_card.get("time_of_day_text_raw")
    confidence = scene_card.get("mapping_confidence", "unknown")

    lines = [
        f"# {scene_id} Pilot Scene Review Packet",
        "",
        "> Do not guess beyond source text.",
        "",
        "## Scene ID",
        "",
        f"`{scene_id}`",
        "",
        "## Grounding Summary",
        "",
        f"- Grounding confidence: `{confidence}`",
        f"- Raw location anchor: `{location_text}`" if location_text else "- Raw location anchor: `_None extracted from opening scene boundary_`",
        f"- Raw time anchor: `{time_text}`" if time_text else "- Raw time anchor: `_None extracted from opening scene boundary_`",
        f"- Raw dialogue characters: {', '.join(f'`{name}`' for name in dialogue_chars) if dialogue_chars else '_None_'}",
        f"- Raw mention characters: {', '.join(f'`{name}`' for name in mention_chars) if mention_chars else '_None_'}",
        "",
        "## Excerpt",
        "",
        "```fountain",
        excerpt_text,
        "```",
        "",
        "## Current Scene Card Fields",
        "",
        "```yaml",
        render_yaml_block(scene_card),
        "```",
        "",
        "## Missing Fields",
        "",
    ]

    if missing:
        lines.extend(f"- `{field}`" for field in missing)
    else:
        lines.append("- `_No placeholder or scaffold fields detected_`")

    lines.extend(["", "## Explicit Human Review Questions", ""])
    lines.extend(f"- {question}" for question in review_questions(scene_id, scene_card, missing))
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- Use the excerpt and retrieval map as the hard grounding boundary.",
            "- If a field cannot be completed without inference, leave it unresolved for a later canon pass.",
            "- Do not introduce Omni-specific fields or visual-dev structures in this review step.",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_packets(scenes_root: Path, output_root: Path) -> int:
    for scene_id in PILOT_SCENES:
        build_packet(scenes_root / scene_id, output_root / f"{scene_id}.md")

    print(f"Pilot scene review packets written: {len(PILOT_SCENES)} scenes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes-root", default="planning/scenes")
    parser.add_argument("--output-root", default="evidence/article3/pilot_scene_review_packets")
    args = parser.parse_args()

    return build_packets(Path(args.scenes_root), Path(args.output_root))


if __name__ == "__main__":
    raise SystemExit(main())
