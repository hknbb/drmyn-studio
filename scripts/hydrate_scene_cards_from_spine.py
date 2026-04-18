from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


SLUGLINE_PREFIX_RE = re.compile(
    r"^(?P<prefix>\.?(?:INT\./EXT\.|EXT\./INT\.|INT/EXT|EXT/INT|INT\.|EXT\.|EST\.|I/E\.))\s*(?P<body>.+)$"
)
SPEAKER_LINE_RE = re.compile(r"^[A-Z][A-Z0-9 .'\-]+(?: \((?:[^)]+)\))?$")
UPPERCASE_NAME_RE = re.compile(r"\b[A-Z][A-Z0-9']*(?: [A-Z][A-Z0-9']*){0,3}\b")
ACTION_LINE_NAME_RE = re.compile(r"^(?P<name>[A-Z][A-Z0-9']*(?: [A-Z][A-Z0-9']*){0,3})(?=[,\s])")
PARENTHETICAL_RE = re.compile(r"\s*\([^)]*\)")

NON_CHARACTER_TOKENS = {
    "END SCENE",
    "SCREEN TEXT",
    "CUT TO",
    "FADE IN",
    "FADE OUT",
    "LATER",
    "CONTINUOUS",
    "DAY",
    "NIGHT",
    "MORNING",
    "AFTERNOON",
    "EVENING",
    "NOON",
    "DAWN",
    "DUSK",
    "PRE-DAWN",
    "MID-MORNING",
    "EARLY MORNING",
    "LATE AFTERNOON",
    "MOMENTS LATER",
    "UNKNOWN",
    "INT",
    "EXT",
    "EST",
    "I/E",
}

PREFERRED_KEY_ORDER = [
    "scene_id",
    "sequence_id",
    "phase_id",
    "beat_id",
    "title",
    "purpose",
    "dramatic_function",
    "location_id",
    "location_text_raw",
    "time_of_day",
    "time_of_day_text_raw",
    "weather",
    "characters_present",
    "characters_explicit_dialogue",
    "characters_explicit_mentions",
    "primary_pov_character",
    "continuity_refs",
    "visual_targets",
    "promptability_score",
    "excerpt_ref",
    "screen_excerpt_ref",
    "prompt_brief_ref",
    "review_notes_ref",
    "source_line_start",
    "source_line_end",
    "source_line_count",
    "anchor_first_nonblank",
    "anchor_last_nonblank",
    "boundary_start_kind",
    "boundary_end_kind",
    "mapping_confidence",
    "notes_grounding",
    "status",
    "review_status",
    "canon_lock",
    "approval",
    "provenance",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    ordered_payload = reorder_mapping(payload)
    rendered = yaml.safe_dump(
        ordered_payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )
    path.write_text(rendered, encoding="utf-8")


def reorder_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in PREFERRED_KEY_ORDER:
        if key in payload:
            ordered[key] = payload[key]
    for key in sorted(payload.keys()):
        if key not in ordered:
            ordered[key] = payload[key]
    return ordered


def extract_fountain_block(markdown_text: str) -> str:
    fence = "```fountain\n"
    start = markdown_text.index(fence) + len(fence)
    end = markdown_text.index("\n```", start)
    return markdown_text[start:end]


def read_scene_excerpt(scene_dir: Path) -> str:
    excerpt_path = scene_dir / "scene_excerpt.md"
    return extract_fountain_block(excerpt_path.read_text(encoding="utf-8"))


def scene_lookup(map_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {scene["scene_id"]: scene for scene in map_data["scenes"]}


def normalized(lines: list[str]) -> list[str]:
    return [line.rstrip("\n") for line in lines]


def first_nonblank_line(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def split_slugline_segments(body: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    bracket_depth = 0

    for char in body:
        if char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)

        if char == "—" and bracket_depth == 0:
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
            continue
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        segments.append(tail)
    return segments


def parse_slugline(line: str) -> dict[str, str] | None:
    match = SLUGLINE_PREFIX_RE.match(line.strip())
    if not match:
        return None

    body = match.group("body").strip()
    segments = split_slugline_segments(body)
    if not segments:
        return None

    if len(segments) == 1:
        location_raw = segments[0]
        time_raw = None
    else:
        location_raw = " — ".join(segments[:-1]).strip()
        time_raw = segments[-1].strip()

    return {
        "prefix": match.group("prefix").lstrip("."),
        "body": body,
        "location_text_raw": location_raw or None,
        "time_of_day_text_raw": time_raw or None,
    }


def first_explicit_slugline(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if parse_slugline(stripped):
            return stripped
    return None


def derive_title(anchor: str, opening_slugline: str | None) -> tuple[str, str]:
    if opening_slugline:
        parsed = parse_slugline(opening_slugline)
        if parsed and parsed["location_text_raw"]:
            return parsed["location_text_raw"][:160], "Title derived from opening slugline location."
        cleaned = opening_slugline[:160]
        return cleaned, "Title derived from opening slugline."

    first_sentence = anchor.split(".")[0].strip()
    if first_sentence:
        return f"{first_sentence}."[:160], "Title derived from opening anchor sentence."
    return anchor[:160], "Title derived from opening anchor fallback."


def normalize_time_of_day(raw_value: str | None) -> str:
    if raw_value is None:
        return "UNKNOWN"

    cleaned = raw_value.strip().upper()
    if cleaned in {"DAWN", "EARLY DAWN", "PRE-DAWN"}:
        return "DAWN"
    if "MORNING" in cleaned:
        return "MORNING"
    if cleaned == "NOON":
        return "NOON"
    if "AFTERNOON" in cleaned:
        return "AFTERNOON"
    if cleaned == "DUSK":
        return "DUSK"
    if "EVENING" in cleaned:
        return "EVENING"
    if cleaned == "NIGHT":
        return "NIGHT"
    return "UNKNOWN"


def clean_speaker_name(line: str) -> str:
    cleaned = PARENTHETICAL_RE.sub("", line).strip()
    return cleaned


def is_slugline(line: str) -> bool:
    return parse_slugline(line) is not None


def is_transition(line: str) -> bool:
    stripped = line.strip()
    return stripped == "---" or stripped.endswith(":")


def detect_dialogue_characters(lines: list[str]) -> list[str]:
    detected: list[str] = []
    seen: set[str] = set()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or is_slugline(stripped) or is_transition(stripped):
            continue
        if not SPEAKER_LINE_RE.match(stripped):
            continue

        speaker = clean_speaker_name(stripped)
        if speaker in NON_CHARACTER_TOKENS:
            continue

        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index >= len(lines):
            continue
        next_line = lines[next_index].strip()
        if is_slugline(next_line) or is_transition(next_line):
            continue

        if speaker not in seen:
            seen.add(speaker)
            detected.append(speaker)

    return detected


def detect_explicit_mentions(lines: list[str]) -> list[str]:
    detected: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or is_slugline(stripped) or is_transition(stripped) or SPEAKER_LINE_RE.match(stripped):
            continue

        match = ACTION_LINE_NAME_RE.match(stripped)
        if not match:
            continue

        normalized_candidate = match.group("name").strip()
        if normalized_candidate in NON_CHARACTER_TOKENS:
            continue
        if len(normalized_candidate) <= 1:
            continue
        if normalized_candidate.isdigit():
            continue
        if normalized_candidate.startswith("SC") and normalized_candidate[2:].isdigit():
            continue
        if normalized_candidate not in seen:
            seen.add(normalized_candidate)
            detected.append(normalized_candidate)

    return detected


def load_numbered_scene_markers(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"#(SC\d{4})#", text))


def hydrate_scene_card(
    scene_card_path: Path,
    prompt_brief_path: Path,
    scene: dict[str, Any],
    numbered_markers: set[str],
) -> dict[str, Any]:
    scene_dir = scene_card_path.parent
    card = load_yaml(scene_card_path) or {}
    excerpt_text = read_scene_excerpt(scene_dir)
    excerpt_lines = normalized(excerpt_text.splitlines())
    excerpt_ref = "scene_excerpt.md"

    first_line = first_nonblank_line(excerpt_lines) or scene["anchor_first_nonblank"]
    opening_slugline = first_line if is_slugline(first_line) else None
    first_slugline_anywhere = first_explicit_slugline(excerpt_lines)
    parsed_opening_slugline = parse_slugline(opening_slugline) if opening_slugline else None
    title, title_note = derive_title(first_line, opening_slugline)

    dialogue_characters = detect_dialogue_characters(excerpt_lines)
    mention_characters = detect_explicit_mentions(excerpt_lines)

    location_text_raw = parsed_opening_slugline["location_text_raw"] if parsed_opening_slugline else None
    time_text_raw = parsed_opening_slugline["time_of_day_text_raw"] if parsed_opening_slugline else None

    notes_grounding = [
        "Hydrated from retrieval map and scene_excerpt.md only.",
        title_note,
    ]
    if opening_slugline:
        notes_grounding.append("Opening slugline provided grounded location/time extraction.")
    else:
        notes_grounding.append("Scene begins without a clear opening slugline; raw location/time left empty.")
    if first_slugline_anywhere and not opening_slugline:
        notes_grounding.append("A later explicit slugline exists inside the excerpt and should be reviewed manually.")
    if scene["mapping_confidence"] != "high":
        notes_grounding.append(f"Retrieval map marks this scene as {scene['mapping_confidence']} confidence.")
    if numbered_markers:
        if scene["scene_id"] in numbered_markers:
            notes_grounding.append("Numbered Fountain marker present for this scene.")
        else:
            notes_grounding.append("Numbered Fountain marker missing; inspect derivative screenplay build.")

    card["scene_id"] = scene["scene_id"]
    card["title"] = title
    card["excerpt_ref"] = excerpt_ref
    card["screen_excerpt_ref"] = excerpt_ref
    card["source_line_start"] = scene["source_line_start"]
    card["source_line_end"] = scene["source_line_end"]
    card["source_line_count"] = scene["source_line_count"]
    card["anchor_first_nonblank"] = scene["anchor_first_nonblank"]
    card["anchor_last_nonblank"] = scene["anchor_last_nonblank"]
    card["boundary_start_kind"] = scene["boundary_start_kind"]
    card["boundary_end_kind"] = scene["boundary_end_kind"]
    card["mapping_confidence"] = scene["mapping_confidence"]
    card["location_text_raw"] = location_text_raw
    card["time_of_day_text_raw"] = time_text_raw
    card["time_of_day"] = normalize_time_of_day(time_text_raw)
    card["characters_explicit_dialogue"] = dialogue_characters
    card["characters_explicit_mentions"] = mention_characters
    card["notes_grounding"] = notes_grounding
    card["status"] = "scaffolded"
    card["review_status"] = "needs_human_review"

    write_yaml(scene_card_path, card)
    prompt_brief_path.write_text(
        render_prompt_brief(
            scene_id=scene["scene_id"],
            anchor=scene["anchor_first_nonblank"],
            raw_slugline=opening_slugline,
            first_slugline_anywhere=first_slugline_anywhere,
            location_text_raw=location_text_raw,
            time_text_raw=time_text_raw,
            dialogue_characters=dialogue_characters,
            mention_characters=mention_characters,
            mapping_confidence=scene["mapping_confidence"],
            boundary_start_kind=scene["boundary_start_kind"],
        ),
        encoding="utf-8",
    )

    return {
        "has_opening_slugline": opening_slugline is not None,
        "fields_filled": {
            "scene_id": 1,
            "title": 1,
            "excerpt_ref": 1,
            "source_line_start": 1,
            "source_line_end": 1,
            "source_line_count": 1,
            "anchor_first_nonblank": 1,
            "anchor_last_nonblank": 1,
            "boundary_start_kind": 1,
            "boundary_end_kind": 1,
            "mapping_confidence": 1,
            "status": 1,
            "review_status": 1,
            "location_text_raw": 1 if location_text_raw else 0,
            "time_of_day_text_raw": 1 if time_text_raw else 0,
            "characters_explicit_dialogue": 1 if dialogue_characters else 0,
            "characters_explicit_mentions": 1 if mention_characters else 0,
            "notes_grounding": 1,
        },
    }


def render_character_list(values: list[str]) -> str:
    if not values:
        return "_None detected_"
    return ", ".join(f"`{value}`" for value in values)


def render_prompt_brief(
    *,
    scene_id: str,
    anchor: str,
    raw_slugline: str | None,
    first_slugline_anywhere: str | None,
    location_text_raw: str | None,
    time_text_raw: str | None,
    dialogue_characters: list[str],
    mention_characters: list[str],
    mapping_confidence: str,
    boundary_start_kind: str,
) -> str:
    lines = [
        f"# {scene_id} Prompt Brief",
        "",
        f"- Scene ID: `{scene_id}`",
        f"- Raw slug / anchor: `{raw_slugline or anchor}`",
        f"- Raw location string: `{location_text_raw}`" if location_text_raw else "- Raw location string: `_None extracted from opening scene boundary_`",
        f"- Raw time-of-day string: `{time_text_raw}`" if time_text_raw else "- Raw time-of-day string: `_None extracted from opening scene boundary_`",
        f"- Boundary start kind: `{boundary_start_kind}`",
        f"- Mapping confidence: `{mapping_confidence}`",
        f"- Explicit dialogue characters: {render_character_list(dialogue_characters)}",
        f"- Explicit mention characters: {render_character_list(mention_characters)}",
    ]
    if first_slugline_anywhere and raw_slugline is None:
        lines.append(f"- First explicit slugline later in excerpt: `{first_slugline_anywhere}`")

    lines.extend(
        [
            "",
            "## Human Review Required",
            "",
            "- Confirm whether the conservative title should be replaced with a reviewed scene label.",
            "- Confirm canonical location/time normalization and any downstream IDs manually.",
            "- Review character extraction against the excerpt before using it in prompts.",
            "- No stylistic, visual, or Omni-specific inference has been added in this stub.",
            "",
            "## Source Links",
            "",
            "- `scene_excerpt.md`",
            "- `planning/manifests/closing_price_scene_retrieval_map.json`",
        ]
    )
    return "\n".join(lines) + "\n"


def hydrate_scenes(
    retrieval_map_path: Path,
    scenes_root: Path,
    report_path: Path,
    numbered_source_path: Path | None,
) -> int:
    map_data = load_json(retrieval_map_path)
    numbered_markers = load_numbered_scene_markers(numbered_source_path)
    lookup = scene_lookup(map_data)

    fields_filled: dict[str, int] = {}
    low_confidence_anchors: list[str] = []
    scenes_missing_clear_slugline_structure: list[str] = []
    scenes_needing_manual_review: list[str] = []
    missing_numbered_markers: list[str] = []

    processed = 0
    for scene_id in sorted(lookup.keys()):
        scene = lookup[scene_id]
        scene_dir = scenes_root / scene_id
        scene_card_path = scene_dir / "scene_card.yaml"
        prompt_brief_path = scene_dir / "prompt_brief.md"

        if not scene_card_path.exists():
            raise FileNotFoundError(f"Missing scene card for {scene_id}: {scene_card_path}")
        if not prompt_brief_path.exists():
            raise FileNotFoundError(f"Missing prompt brief for {scene_id}: {prompt_brief_path}")
        if not (scene_dir / "scene_excerpt.md").exists():
            raise FileNotFoundError(f"Missing scene excerpt for {scene_id}: {scene_dir / 'scene_excerpt.md'}")

        result = hydrate_scene_card(
            scene_card_path=scene_card_path,
            prompt_brief_path=prompt_brief_path,
            scene=scene,
            numbered_markers=numbered_markers,
        )

        processed += 1
        for key, value in result["fields_filled"].items():
            fields_filled[key] = fields_filled.get(key, 0) + value

        if scene["mapping_confidence"] != "high":
            low_confidence_anchors.append(scene_id)
        if not result["has_opening_slugline"]:
            scenes_missing_clear_slugline_structure.append(scene_id)
        scenes_needing_manual_review.append(scene_id)
        if numbered_markers and scene_id not in numbered_markers:
            missing_numbered_markers.append(scene_id)

    report_payload = {
        "fields_filled": fields_filled,
        "numbered_fountain_validation": {
            "checked": bool(numbered_markers),
            "missing_scene_markers": missing_numbered_markers,
        },
        "scenes_missing_clear_slugline_structure": scenes_missing_clear_slugline_structure,
        "scenes_needing_manual_review": scenes_needing_manual_review,
        "scenes_processed": processed,
        "scenes_with_low_confidence_anchors": low_confidence_anchors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    print(
        "Scene hydration complete:",
        f"{processed} scenes processed,",
        f"{len(low_confidence_anchors)} low-confidence anchors,",
        f"{len(scenes_missing_clear_slugline_structure)} scenes without clear opening sluglines,",
        f"{len(scenes_needing_manual_review)} scenes flagged for human review",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retrieval-map",
        default="planning/manifests/closing_price_scene_retrieval_map.json",
        help="Path to the authoritative scene retrieval map.",
    )
    parser.add_argument(
        "--scenes-root",
        default="planning/scenes",
        help="Root directory containing SCxxxx scene folders.",
    )
    parser.add_argument(
        "--numbered-source",
        default="source/screenplay/closing_price.numbered.fountain",
        help="Optional numbered Fountain derivative used for marker validation.",
    )
    parser.add_argument(
        "--report",
        default="evidence/validation_reports/scene_hydration_report.json",
        help="Where to write the deterministic hydration report.",
    )
    args = parser.parse_args()

    numbered_source = Path(args.numbered_source)
    return hydrate_scenes(
        retrieval_map_path=Path(args.retrieval_map),
        scenes_root=Path(args.scenes_root),
        report_path=Path(args.report),
        numbered_source_path=numbered_source if numbered_source.exists() else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
