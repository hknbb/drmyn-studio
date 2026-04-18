from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCENE_ID_RE = re.compile(r"^SC\d{4}$")
SCENE_NUMBER_SUFFIX_RE = re.compile(r"\s+#([A-Za-z0-9_-]+)#$")
SLUGLINE_RE = re.compile(r"^(INT|EXT|EST|I/E|INT/EXT|EXT/INT)\.")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text_lines(path: Path) -> tuple[list[str], bool]:
    text = path.read_text(encoding="utf-8")
    return text.splitlines(), text.endswith("\n")


def write_text_lines(path: Path, lines: list[str], had_trailing_newline: bool) -> None:
    rendered = "\n".join(lines)
    if had_trailing_newline or rendered:
        rendered = f"{rendered}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def ignored_prefix_offset(map_data: dict[str, Any]) -> int:
    source_file = map_data.get("source_file", {})
    ignored_lines = source_file.get("ignored_prefix_lines", [])
    return len(ignored_lines)


def normalized_scene_starts(map_data: dict[str, Any], total_lines: int) -> dict[int, dict[str, Any]]:
    offset = ignored_prefix_offset(map_data)
    starts: dict[int, dict[str, Any]] = {}

    for scene in map_data["scenes"]:
        scene_id = scene["scene_id"]
        if not SCENE_ID_RE.match(scene_id):
            raise ValueError(f"Malformed scene_id in retrieval map: {scene_id}")

        line_number = scene["source_line_start"] - offset
        if line_number < 1 or line_number > total_lines:
            raise ValueError(
                f"{scene_id} start line {scene['source_line_start']} normalizes to invalid line {line_number}."
            )

        if line_number in starts:
            other = starts[line_number]["scene_id"]
            raise ValueError(f"Duplicate normalized start line {line_number}: {other}, {scene_id}")

        starts[line_number] = scene

    return starts


def strip_scene_number_suffix(line: str) -> str:
    return SCENE_NUMBER_SUFFIX_RE.sub("", line.rstrip())


def is_scene_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("."):
        return True
    return bool(SLUGLINE_RE.match(stripped))


def render_numbered_heading(line: str, scene_id: str) -> str:
    return f"{strip_scene_number_suffix(line)} #{scene_id}#"


def heading_seed_text(last_heading: str | None, fallback_anchor: str) -> str:
    base = last_heading or fallback_anchor
    stripped = strip_scene_number_suffix(base.strip()).lstrip(".").strip()
    return stripped or fallback_anchor.strip() or "SCENE"


def build_numbered_lines(master_lines: list[str], map_data: dict[str, Any]) -> list[str]:
    scene_starts = normalized_scene_starts(map_data, total_lines=len(master_lines))
    output: list[str] = []
    last_heading: str | None = None

    for index, line in enumerate(master_lines, start=1):
        scene = scene_starts.get(index)
        if scene is not None:
            anchor = scene["anchor_first_nonblank"].strip()
            line_text = line.strip()
            anchor_matches = (
                line_text == anchor
                or line_text.startswith(anchor)
                or anchor.startswith(line_text)
            )
            if not anchor_matches:
                raise ValueError(
                    f"{scene['scene_id']} expected anchor '{anchor}' at line {index}, found '{line_text}'."
                )

            if scene["boundary_start_kind"] in {"slug", "cont_slug"} and is_scene_heading(line):
                numbered_heading = render_numbered_heading(line, scene["scene_id"])
                output.append(numbered_heading)
                last_heading = strip_scene_number_suffix(line).strip().lstrip(".")
                continue

            synthetic_base = heading_seed_text(last_heading, fallback_anchor=anchor)
            output.append(f".{synthetic_base} #{scene['scene_id']}#")

        output.append(line)

        if is_scene_heading(line):
            last_heading = strip_scene_number_suffix(line).strip().lstrip(".")

    return output


def build_numbered_fountain(
    source_path: Path,
    retrieval_map_path: Path,
    output_path: Path,
) -> int:
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Output path must differ from the master Fountain path.")

    master_lines, had_trailing_newline = read_text_lines(source_path)
    map_data = load_json(retrieval_map_path)
    numbered_lines = build_numbered_lines(master_lines, map_data)
    write_text_lines(output_path, numbered_lines, had_trailing_newline=had_trailing_newline)

    synthetic_scene_count = sum(
        1 for scene in map_data["scenes"] if scene["boundary_start_kind"] not in {"slug", "cont_slug"}
    )
    print(
        "Numbered Fountain written:",
        output_path,
        f"({len(map_data['scenes'])} spine scenes, {synthetic_scene_count} synthetic continuity markers)",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default="source/screenplay/closing_price.fountain",
        help="Path to the canonical unnumbered Fountain screenplay.",
    )
    parser.add_argument(
        "--retrieval-map",
        default="planning/manifests/closing_price_scene_retrieval_map.json",
        help="Path to the authoritative scene spine retrieval map.",
    )
    parser.add_argument(
        "--output",
        default="source/screenplay/closing_price.numbered.fountain",
        help="Path for the generated numbered Fountain derivative.",
    )
    args = parser.parse_args()

    return build_numbered_fountain(
        source_path=Path(args.source),
        retrieval_map_path=Path(args.retrieval_map),
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    raise SystemExit(main())
