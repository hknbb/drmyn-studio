"""inject_render_fields_sc0047.py

Add render_* fields (kling_literal_alias_locked) to SC0047 omni_clip_manifest files
and update the scene_continuity_ledger with render_start_state / render_end_state.

Also fixes legacy required_element_id references:
  PROP047 -> PROP008  (handset was registered as PROP008, not PROP047)
  LOC001  -> LOC006   (this scene is at LOC006 quay, not LOC001 nursery)

Usage:
    python scripts/inject_render_fields_sc0047.py [--dry-run]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[1]
SCENE = "SC0047"
DRY_RUN = "--dry-run" in sys.argv

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.width = 4096


def write_yaml(path: Path, data: object) -> None:
    if DRY_RUN:
        print(f"  [dry-run] {path.name}")
        return
    buf = io.StringIO()
    yaml.dump(data, buf)
    path.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    print(f"  written: {path.name}")


def fix_elem_ids(ids: list) -> list:
    """Fix legacy element ID references."""
    result = []
    for r in ids or []:
        if r == "PROP047":
            result.append("PROP008")
        elif r == "LOC001":
            result.append("LOC006")
        else:
            result.append(r)
    return result


# ---------------------------------------------------------------------------
# Per-shot render data keyed by shot_id
# All text is kling_literal_alias_locked:
#   - alias-only (@C01_NADIA, @C09_OTTO, @LOC006_QUAY, @PROP008_HANDSET)
#   - no role nouns (man/woman/contact/protagonist)
#   - no metaphors / abstract language
#   - no bare "center/centered" as positional labels
# ---------------------------------------------------------------------------
SHOT_RENDER: dict[str, dict] = {
    # CLIP 01 — establish quay bay + Nadia arrives
    "SHOT_SC0047_01_A": {
        "render_action": (
            "A converted freight bay in @LOC006_QUAY — low concrete ceiling, "
            "one high window facing the quay, salt-weathered concrete floor. "
            "No people in frame. Morning light through the high window; grey water visible outside."
        ),
        "render_camera": "Wide shot, static.",
        "render_diegetic_audio": "low ambient room tone; distant water sound from beyond the high window.",
    },
    "SHOT_SC0047_01_B": {
        "render_action": (
            "@C09_OTTO stands in @LOC006_QUAY near the folding table, arms at his sides. "
            "@C01_NADIA enters through the doorway and stops just inside. "
            "@C09_OTTO does not move toward @C01_NADIA; stands still, facing forward."
        ),
        "render_camera": "Medium two-shot, static.",
        "render_diegetic_audio": "footsteps on concrete as @C01_NADIA enters; room tone holds.",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": "stands near the table, arms at his sides, not gesturing.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "enters through the doorway and stops just inside, facing @C09_OTTO.",
            }
        ],
        "add_elem_ids": ["C01"],
    },
    # CLIP 02 — Otto speaks + produces handset + code line
    "SHOT_SC0047_02_A": {
        "render_action": (
            "@C09_OTTO and @C01_NADIA face each other across the folding table. "
            "@C09_OTTO lips move; @C01_NADIA is still, listening. Neither gestures."
        ),
        "render_camera": "Medium two-shot, static.",
        "render_diegetic_audio": "@C09_OTTO speaks; dialogue audio suppressed (Format A).",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": "faces @C01_NADIA across the table, lips moving, not gesturing.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "faces @C09_OTTO across the table, still, listening.",
            }
        ],
    },
    "SHOT_SC0047_02_B": {
        "render_action": (
            "@C09_OTTO reaches beneath the folding table with both hands, lifts a locked case "
            "onto the table surface, and opens it. @C09_OTTO removes @PROP008_HANDSET — "
            "a plain industrial handset with no markings — and sets @PROP008_HANDSET on the table between them."
        ),
        "render_camera": "Medium shot on the table, static.",
        "render_diegetic_audio": "case latch opening; @PROP008_HANDSET placed on the table; room tone holds.",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": (
                    "lifts a locked case from beneath the table, opens it, "
                    "removes @PROP008_HANDSET, and sets it on the table."
                ),
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
    },
    "SHOT_SC0047_02_C": {
        "render_action": (
            "@C09_OTTO and @C01_NADIA face each other across the table; "
            "@PROP008_HANDSET lies on the table between them. "
            "@C09_OTTO lips move; @C01_NADIA lips move in a brief reply. "
            "Neither picks up @PROP008_HANDSET."
        ),
        "render_camera": "Over-shoulder medium close on @C09_OTTO, static.",
        "render_diegetic_audio": "@C09_OTTO and @C01_NADIA speak in sequence; dialogue audio suppressed (Format A).",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": "faces @C01_NADIA; lips move.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "faces @C09_OTTO across the table; lips move briefly in reply.",
            }
        ],
    },
    # CLIP 03 — Otto gives privacy; Nadia enters code
    "SHOT_SC0047_03_A": {
        "render_action": (
            "@C09_OTTO turns from the folding table and walks to the far end of @LOC006_QUAY. "
            "@C09_OTTO stops at the high window, turns to face the glass, and holds still there."
        ),
        "render_camera": "Medium-wide shot tracking @C09_OTTO to the window, settling static.",
        "render_diegetic_audio": "footsteps on concrete; room tone; water sound from beyond the high window.",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": "turns from the table, walks to the high window, stops facing the glass.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
    },
    "SHOT_SC0047_03_B": {
        "render_action": (
            "@C01_NADIA stands at the folding table; @PROP008_HANDSET is on the table. "
            "@C01_NADIA's fingers press the keypad — five keystrokes. "
            "@PROP008_HANDSET screen activates. @C01_NADIA presses the play button."
        ),
        "render_camera": "Close shot on @C01_NADIA face and hands, rack focus.",
        "render_diegetic_audio": "keypad tones; a soft electronic activation chime from @PROP008_HANDSET.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "picks up @PROP008_HANDSET, presses five digits, then presses play.",
            },
        },
    },
    # CLIP 04 — Marcus V.O. opens (Nadia listens, one long shot)
    "SHOT_SC0047_04_A": {
        "render_action": (
            "@C01_NADIA stands at the folding table, @PROP008_HANDSET in her hand. "
            "@C01_NADIA does not move; her eyes are fixed on @PROP008_HANDSET."
        ),
        "render_camera": "Medium-close shot on @C01_NADIA, static.",
        "render_diegetic_audio": "low wind ambient from @PROP008_HANDSET; room tone holds; @PROP008_HANDSET audio plays (Format A — V.O. audio suppressed).",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "stands at the table, @PROP008_HANDSET in her hand, eyes fixed on the screen, not moving.",
            }
        ],
    },
    # CLIP 05 — Marcus V.O. details partition (long hold on Nadia)
    "SHOT_SC0047_05_A": {
        "render_action": (
            "@C01_NADIA stands at the folding table, @PROP008_HANDSET in her hand. "
            "@C01_NADIA keeps her eyes on @PROP008_HANDSET; she does not shift weight, "
            "does not look up, does not change her grip."
        ),
        "render_camera": "Medium-close shot on @C01_NADIA face and hands, static.",
        "render_diegetic_audio": "@PROP008_HANDSET audio continues (Format A — V.O. audio suppressed); room tone holds.",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "stands still at the table, @PROP008_HANDSET in both hands, eyes on the screen.",
            }
        ],
    },
    # CLIP 06 — Marcus V.O. names broadcast target (Nadia absorbs)
    "SHOT_SC0047_06_A": {
        "render_action": (
            "@C01_NADIA stands at the folding table, @PROP008_HANDSET held in both hands. "
            "@C01_NADIA's jaw tightens; she gives a single small downward nod. "
            "@C01_NADIA does not speak; does not move from the table."
        ),
        "render_camera": "Medium-close shot on @C01_NADIA, static.",
        "render_diegetic_audio": "@PROP008_HANDSET audio continues, nearing its end (Format A — V.O. audio suppressed); room tone holds.",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "stands at the table, @PROP008_HANDSET in both hands, jaw tightening, a single nod downward.",
            }
        ],
    },
    # CLIP 07 — Marcus's last words; silence holds
    "SHOT_SC0047_07_A": {
        "render_action": (
            "@C01_NADIA holds @PROP008_HANDSET in both hands; @C09_OTTO stands at the far window, back to the room. "
            "The recording on @PROP008_HANDSET ends. @C01_NADIA keeps @PROP008_HANDSET in both hands; does not put it down. "
            "@C09_OTTO does not turn."
        ),
        "render_camera": "Medium-close shot on @C01_NADIA with @C09_OTTO out of focus in background, static.",
        "render_diegetic_audio": "final audio from @PROP008_HANDSET ends; then silence; no ambient sound.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "keeps @PROP008_HANDSET in both hands as the recording ends; does not put it down.",
            },
            "FIG_OTTO": {
                "render_action": "stands at the far window, back to the room, does not turn.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
        },
    },
    "SHOT_SC0047_07_B": {
        "render_action": (
            "@C01_NADIA holds @PROP008_HANDSET in both hands, screen facing up. "
            "@C01_NADIA does not move; her eyes are on the screen; her jaw is set; she breathes slowly."
        ),
        "render_camera": "Close shot on @C01_NADIA face, static.",
        "render_diegetic_audio": "silence holds; a slow controlled breath from @C01_NADIA.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "holds @PROP008_HANDSET in both hands, still, jaw set, eyes on the screen.",
            },
        },
    },
    # CLIP 08 — Nadia opens partition, begins reading
    "SHOT_SC0047_08_A": {
        "render_action": (
            "@C01_NADIA taps a second code into @PROP008_HANDSET keypad. "
            "@PROP008_HANDSET screen changes; a partition opens. "
            "@C01_NADIA tilts @PROP008_HANDSET and begins reading from the screen; her thumb scrolls."
        ),
        "render_camera": "Close shot on @C01_NADIA hands and @PROP008_HANDSET, slow drift to close on @C01_NADIA face.",
        "render_diegetic_audio": "soft keypad tone; partition chime from @PROP008_HANDSET; then ambient return — water sound from the high window of @LOC006_QUAY.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "enters a second code, opens the partition, and begins reading from @PROP008_HANDSET screen.",
            },
        },
    },
    # CLIP 09 — Otto/Nadia brief exchange; Nadia returns to reading
    "SHOT_SC0047_09_A": {
        "render_action": (
            "@C09_OTTO turns from the high window of @LOC006_QUAY and faces @C01_NADIA. "
            "@C09_OTTO and @C01_NADIA exchange brief lines; "
            "@C01_NADIA answers without looking up from @PROP008_HANDSET; @C09_OTTO nods. "
            "@C09_OTTO speaks once more; @C01_NADIA looks up briefly and replies. "
            "@C09_OTTO turns back toward the window. @C01_NADIA returns to @PROP008_HANDSET."
        ),
        "render_camera": "Medium two-shot, static.",
        "render_diegetic_audio": "room tone; @C09_OTTO and @C01_NADIA exchange brief lines (Format A — dialogue audio suppressed); room tone returns.",
        "figure_render": {
            "FIG_OTTO": {
                "render_action": "turns from the window to face @C01_NADIA, speaks, nods, then turns back to the window.",
                "render_label": "weathered grey jacket, close-kept grey hair.",
            },
            "FIG_NADIA": {
                "render_action": "answers @C09_OTTO without looking up; looks up briefly for one reply; returns to reading @PROP008_HANDSET.",
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Continuity ledger render states (alias-locked, no role nouns, no bare center)
# ---------------------------------------------------------------------------
LEDGER_RENDER: dict[str, dict] = {
    "CLIP_SC0047_01": {
        "render_start_state": "@LOC006_QUAY empty; high window with grey water visible outside; no figures in frame.",
        "render_end_state": "@C01_NADIA inside the doorway; @C09_OTTO near the table; the freight bay established.",
    },
    "CLIP_SC0047_02": {
        "render_start_state": "@C01_NADIA inside the doorway; @C09_OTTO near the table, facing her.",
        "render_end_state": "@PROP008_HANDSET on the table between @C09_OTTO and @C01_NADIA; neither has picked it up.",
    },
    "CLIP_SC0047_03": {
        "render_start_state": "@PROP008_HANDSET on the table; @C09_OTTO on one side, @C01_NADIA on the other side.",
        "render_end_state": "@C01_NADIA holding @PROP008_HANDSET with audio active; @C09_OTTO at the far-end window, back to the room.",
    },
    "CLIP_SC0047_04": {
        "render_start_state": "@C01_NADIA at the table, @PROP008_HANDSET in her hand; @C09_OTTO at the window, back to the room.",
        "render_end_state": "@C01_NADIA standing, @PROP008_HANDSET held in both hands; @C09_OTTO background at the window.",
    },
    "CLIP_SC0047_05": {
        "render_start_state": "@C01_NADIA standing at the table, @PROP008_HANDSET in both hands; @C09_OTTO background at the window.",
        "render_end_state": "@C01_NADIA standing, @PROP008_HANDSET in both hands; unchanged; @C09_OTTO background at the window.",
    },
    "CLIP_SC0047_06": {
        "render_start_state": "@C01_NADIA standing, @PROP008_HANDSET in both hands; @C09_OTTO at the window.",
        "render_end_state": "@C01_NADIA standing at the table, @PROP008_HANDSET held; the recording on @PROP008_HANDSET nearly finished.",
    },
    "CLIP_SC0047_07": {
        "render_start_state": "@C01_NADIA at the table, @PROP008_HANDSET held; @C09_OTTO background at the window.",
        "render_end_state": "@C01_NADIA standing, @PROP008_HANDSET in both hands, in silence; @C09_OTTO background at the window.",
    },
    "CLIP_SC0047_08": {
        "render_start_state": "@C01_NADIA standing, @PROP008_HANDSET in both hands, in silence; @C09_OTTO background at the window.",
        "render_end_state": "@C01_NADIA reading from @PROP008_HANDSET partition at the table; @C09_OTTO background at the window.",
    },
    "CLIP_SC0047_09": {
        "render_start_state": "@C01_NADIA reading @PROP008_HANDSET at the table; @C09_OTTO at the window, back to the room.",
        "render_end_state": "@C01_NADIA reading @PROP008_HANDSET at the table; @C09_OTTO near the window; scene closed.",
    },
}


def inject_manifest(clip_id: str) -> None:
    path = (
        REPO / "planning" / "scenes" / SCENE / "manifests" / f"{clip_id}_manifest.yaml"
    )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh)

    shots = data.get("shots") or []
    for shot in shots:
        shot_id = shot.get("shot_id")
        if not isinstance(shot_id, str) or shot_id not in SHOT_RENDER:
            continue
        rd = SHOT_RENDER[shot_id]

        # Add render_* fields at shot level
        shot["render_action"] = rd["render_action"]
        shot["render_camera"] = rd["render_camera"]
        shot["render_diegetic_audio"] = rd["render_diegetic_audio"]

        # Fix required_element_ids at shot level
        if "required_element_ids" in shot:
            shot["required_element_ids"] = fix_elem_ids(shot["required_element_ids"])

        # Add extra element IDs if needed
        extra = rd.get("add_elem_ids", [])
        if extra and "required_element_ids" in shot:
            existing = list(shot["required_element_ids"])
            for eid in extra:
                if eid not in existing:
                    existing.append(eid)
            shot["required_element_ids"] = existing

        # Update figure render fields
        fig_render = rd.get("figure_render", {})
        for fig in shot.get("figures") or []:
            fid = fig.get("figure_id")
            if fid in fig_render:
                for k, v in fig_render[fid].items():
                    fig[k] = v

        # Add missing figures
        add_figs = rd.get("add_figures", [])
        if add_figs:
            existing_aliases = {
                f.get("kling_alias") for f in (shot.get("figures") or [])
            }
            if "figures" not in shot or shot["figures"] is None:
                shot["figures"] = []
            for af in add_figs:
                if af.get("kling_alias") not in existing_aliases:
                    # Add render_* from figure_render if available
                    fid = af.get("figure_id")
                    merged = dict(af)
                    if fid in fig_render:
                        for k, v in fig_render[fid].items():
                            merged[k] = v
                    shot["figures"].append(merged)

    # Fix clip-level required_element_ids
    if "required_element_ids" in data:
        data["required_element_ids"] = fix_elem_ids(data["required_element_ids"])

    # Update notes and provenance
    data["notes"] = (
        "SC0047 v07 text-only literal pass (kling_literal_alias_locked): "
        "render_* fields authored for model-facing literal grammar; "
        "poetic prompt_action/lens_bias/diegetic_audio remain for human review only. "
        "Legacy element ID refs fixed: PROP047→PROP008, LOC001→LOC006."
    )
    prov = data.get("provenance") or {}
    prov["render_fields_added_by"] = "claude_code (M5 v07 SC0047 literal pass)"
    prov["render_fields_added_at"] = "2026-06-17T00:00:00Z"
    data["provenance"] = prov

    write_yaml(path, data)


def update_ledger() -> None:
    path = REPO / "planning" / "scenes" / SCENE / "scene_continuity_ledger.yaml"
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh)

    for entry in data.get("clip_chain") or []:
        clip_id = entry.get("clip_id")
        if clip_id in LEDGER_RENDER:
            lr = LEDGER_RENDER[clip_id]
            entry["render_start_state"] = lr["render_start_state"]
            entry["render_end_state"] = lr["render_end_state"]

    write_yaml(path, data)


def main() -> None:
    manifests_dir = REPO / "planning" / "scenes" / SCENE / "manifests"
    clip_ids = sorted(
        p.stem.replace("_manifest", "")
        for p in manifests_dir.glob("CLIP_*.yaml")
    )
    print(f"=== SC0047 render_* field injection {'(DRY RUN) ' if DRY_RUN else ''}===")
    print(f"Found {len(clip_ids)} manifests.")
    for clip_id in clip_ids:
        inject_manifest(clip_id)
    print("Updating scene_continuity_ledger ...")
    update_ledger()
    print("Done.")


if __name__ == "__main__":
    main()
