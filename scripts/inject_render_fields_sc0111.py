"""inject_render_fields_sc0111.py

Add render_* fields (kling_literal_alias_locked) to SC0111 omni_clip_manifest files
and update the scene_continuity_ledger with render_start_state / render_end_state.

No legacy element ID bugs in SC0111 manifests.

Active aliases for SC0111:
  @C01_NADIA (battle-worn compound look), @C02_ROMAN, @LOC007_ANTECHAMBER
  No dialogue in SC0111 — silent close-quarters fight; Format A throughout.

Usage:
    python scripts/inject_render_fields_sc0111.py [--dry-run]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[1]
SCENE = "SC0111"
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


# ---------------------------------------------------------------------------
# Per-shot render data keyed by shot_id
# All text is kling_literal_alias_locked:
#   - alias-only (@C01_NADIA, @C02_ROMAN, @LOC007_ANTECHAMBER)
#   - no role nouns (protagonist, antagonist, enemy, opponent)
#   - no metaphors / abstract language
#   - no bare "center/centered" as positional labels
#   - no dialogue (scene is silent action throughout)
# ---------------------------------------------------------------------------
SHOT_RENDER: dict[str, dict] = {
    # ------------------------------------------------------------------
    # CLIP 01 — Establish adjustment; third approach
    # ------------------------------------------------------------------
    "SHOT_SC0111_01_A": {
        "render_action": (
            "@LOC007_ANTECHAMBER narrow concrete corridor, server-core surface at the far end. "
            "@C01_NADIA and @C02_ROMAN face each other at close range. "
            "@C01_NADIA's left arm is held closer to her body — not extended. "
            "@C02_ROMAN's stance is low, weight balanced. Both breathing visible. No contact."
        ),
        "render_camera": "Medium-wide static. Both figures in corridor. @LOC007_ANTECHAMBER walls tight on both sides.",
        "render_diegetic_audio": "Controlled breathing from both. Cool corridor ambient. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA faces @C02_ROMAN, left arm held close to body, breathing visible.",
                "render_label": "battle-worn field jacket, left arm limited range.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN faces @C01_NADIA, stance low, watching.",
                "render_label": "dark close-fitted jacket, weight low.",
            },
        },
    },
    "SHOT_SC0111_01_B": {
        "render_action": (
            "@C02_ROMAN steps in — approach line is low, below @C01_NADIA's sternum, "
            "inside the deflection arc of @C01_NADIA's left arm. "
            "@C01_NADIA's right arm moves to deflect. @C01_NADIA's left arm cannot cover the approach line."
        ),
        "render_camera": "Medium-close handheld. Contact level. Lower approach angle of @C02_ROMAN visible.",
        "render_diegetic_audio": "Controlled breathing. Fabric contact impact.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA deflects with right arm; left arm held, not reaching the line.",
                "render_label": "battle-worn field jacket, left arm limited range.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN steps in low — below sternum line, inside @C01_NADIA's left-arm range.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 02 — Floor seam; door frame
    # ------------------------------------------------------------------
    "SHOT_SC0111_02_A": {
        "render_action": (
            "@C02_ROMAN advances, driving @C01_NADIA toward the far wall. "
            "@C02_ROMAN's footwork follows a diagonal, not the shortest path — angling @C01_NADIA "
            "toward a floor seam. @C01_NADIA retreats, managing her left side."
        ),
        "render_camera": "Medium tracking. Floor surface visible. @C01_NADIA retreating on diagonal.",
        "render_diegetic_audio": "Footsteps on concrete. Controlled breathing.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA retreats, left side managed, feet adjusting to diagonal floor.",
                "render_label": "battle-worn field jacket, left arm limited range.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN advances on diagonal, driving @C01_NADIA toward the corridor wall.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    "SHOT_SC0111_02_B": {
        "render_action": (
            "@C01_NADIA's right shoulder contacts the door frame — controlled into it, not thrown. "
            "@C01_NADIA's back is against the frame; server-core door behind her. "
            "@C02_ROMAN stands 60cm in front, not making contact. Geometry has closed the space."
        ),
        "render_camera": "Medium handheld. @C01_NADIA's back against door frame. Corridor walls visible on both sides.",
        "render_diegetic_audio": "Right shoulder contacting frame. Controlled breathing — @C01_NADIA managing cost.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA's right shoulder against door frame, back to server-core door.",
                "render_label": "battle-worn field jacket, left arm limited range.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN stands 60cm from @C01_NADIA, facing her, not touching — geometry did the work.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 03 — Breathing cost (long hold)
    # ------------------------------------------------------------------
    "SHOT_SC0111_03_A": {
        "render_action": (
            "@C01_NADIA's chest rises and falls — each breath visible, each inhale a controlled decision. "
            "@C01_NADIA's left arm stays close to her body. "
            "@C02_ROMAN stands 1 meter away, still, watching. No new contact."
        ),
        "render_camera": "Medium-close static. @C01_NADIA's chest and breathing dominant. @C02_ROMAN at right edge.",
        "render_diegetic_audio": "Labored controlled breathing from @C01_NADIA. @C02_ROMAN breathing even. Corridor ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA breathing visibly, left arm close, back still against frame.",
                "render_label": "battle-worn field jacket, left arm limited range.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN stands still 1 meter from @C01_NADIA, weight low, watching.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 04 — Geometry closed; decision point (Nadia only)
    # ------------------------------------------------------------------
    "SHOT_SC0111_04_A": {
        "render_action": (
            "@C01_NADIA's eyes hold @C02_ROMAN's position. @C01_NADIA's jaw sets. "
            "@C01_NADIA does not move yet. @C01_NADIA's right hand opens once, then closes."
        ),
        "render_camera": "Medium-close static. @C01_NADIA face. Eyes tracking @C02_ROMAN's position.",
        "render_diegetic_audio": "Controlled breathing. Silence. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA jaw sets, eyes holding @C02_ROMAN's position, right hand opens and closes.",
                "render_label": "battle-worn field jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 05 — Bilateral hold applied (long hold)
    # ------------------------------------------------------------------
    "SHOT_SC0111_05_A": {
        "render_action": (
            "@C01_NADIA steps forward — one step, closing distance. "
            "@C01_NADIA's both thumbs press against opposite sides of @C02_ROMAN's neck at jaw angle. "
            "@C01_NADIA holds — arms engaged, sustained pressure, not a strike. "
            "@C02_ROMAN's hands reach @C01_NADIA's forearms and grip — but do not break the hold. "
            "@C02_ROMAN remains upright."
        ),
        "render_camera": "Close static. Tight on the hold. @C01_NADIA's arms extended. @C02_ROMAN's hands on @C01_NADIA's forearms.",
        "render_diegetic_audio": "Strained muscle effort. @C02_ROMAN's breathing changing rhythm. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA both thumbs on @C02_ROMAN's neck at jaw angle, sustained, arms engaged.",
                "render_label": "battle-worn field jacket.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN's hands grip @C01_NADIA's forearms, grip active but hold not broken.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 06 — Hold sustained; vasovagal descent
    # ------------------------------------------------------------------
    "SHOT_SC0111_06_A": {
        "render_action": (
            "@C01_NADIA maintains bilateral thumb pressure on @C02_ROMAN's neck. "
            "@C02_ROMAN's hands continue on @C01_NADIA's forearms — grip weakening. "
            "@C02_ROMAN is still upright. Both bodies locked."
        ),
        "render_camera": "Medium-close static. Hold sustained. @C02_ROMAN's face visible — body response beginning.",
        "render_diegetic_audio": "Sustained effort. @C02_ROMAN's breathing slowing.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA maintains hold — both thumbs sustained on @C02_ROMAN's neck.",
                "render_label": "battle-worn field jacket.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN upright, hands on @C01_NADIA's forearms, grip weakening.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    "SHOT_SC0111_06_B": {
        "render_action": (
            "@C02_ROMAN's knees unlock — legs lose load in a controlled descent, not a fall. "
            "@C02_ROMAN descends to the corridor floor. "
            "@C01_NADIA goes with @C02_ROMAN — one knee on concrete. "
            "@C01_NADIA releases thumb pressure as @C02_ROMAN reaches the floor. "
            "@C01_NADIA remains on one knee."
        ),
        "render_camera": "Medium handheld. Both descending. Corridor floor. @C01_NADIA one knee down.",
        "render_diegetic_audio": "Bodies controlled to floor. Release of held breath.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA goes down with @C02_ROMAN, one knee on floor, releases pressure as @C02_ROMAN lands.",
                "render_label": "battle-worn field jacket.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN descends to floor — knees unlock, controlled loss of load-bearing.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 07 — Nadia rises (Nadia only)
    # ------------------------------------------------------------------
    "SHOT_SC0111_07_A": {
        "render_action": (
            "@C01_NADIA on one knee on corridor floor. "
            "@C01_NADIA presses right palm to the ground. "
            "@C01_NADIA's left side held close — not extending left arm. "
            "@C01_NADIA shifts weight right and rises to both feet. @C01_NADIA stands."
        ),
        "render_camera": "Medium-close handheld. @C01_NADIA rising from floor. Left side protection visible.",
        "render_diegetic_audio": "Controlled exhale on rise. Single footstep as @C01_NADIA stands.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA presses right palm to floor, left arm held in, rises to both feet.",
                "render_label": "battle-worn field jacket.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 08 — Roman on floor; Nadia standing; she moves
    # ------------------------------------------------------------------
    "SHOT_SC0111_08_A": {
        "render_action": (
            "@C02_ROMAN on corridor floor — back flat, chest rising and falling. "
            "@C01_NADIA stands upright 2 meters from @C02_ROMAN, facing @C02_ROMAN. "
            "@C01_NADIA watches @C02_ROMAN's chest. "
            "@C01_NADIA turns and steps toward the corridor end."
        ),
        "render_camera": "Medium-wide static. @C01_NADIA standing, @C02_ROMAN on floor. @LOC007_ANTECHAMBER corridor behind and ahead.",
        "render_diegetic_audio": "Controlled breathing from @C01_NADIA. @C02_ROMAN's chest rhythm. Corridor ambient. Then a footstep as @C01_NADIA moves.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA stands 2m from @C02_ROMAN, watches chest, then turns and steps toward corridor end.",
                "render_label": "battle-worn field jacket.",
            },
            "FIG_ROMAN": {
                "render_action": "@C02_ROMAN on corridor floor, back flat, chest rising and falling.",
                "render_label": "dark close-fitted jacket.",
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Continuity ledger render states (alias-locked, no role nouns, no bare center)
# ---------------------------------------------------------------------------
LEDGER_RENDER: dict[str, dict] = {
    "CLIP_SC0111_01": {
        "render_start_state": "@C01_NADIA and @C02_ROMAN facing each other in @LOC007_ANTECHAMBER. @C01_NADIA's left arm held close.",
        "render_end_state": "@C02_ROMAN approaching below @C01_NADIA's sternum line. @C01_NADIA's left arm unable to cover approach.",
    },
    "CLIP_SC0111_02": {
        "render_start_state": "@C02_ROMAN advancing on diagonal. @C01_NADIA retreating toward far wall.",
        "render_end_state": "@C01_NADIA's back against door frame, server-core door behind. @C02_ROMAN controlling space in front.",
    },
    "CLIP_SC0111_03": {
        "render_start_state": "@C01_NADIA against door frame. @C02_ROMAN 1m away, still, watching.",
        "render_end_state": "@C01_NADIA breathing with cost. @C02_ROMAN waiting. No new contact.",
    },
    "CLIP_SC0111_04": {
        "render_start_state": "@C01_NADIA against frame, geometry closed. @C02_ROMAN in front.",
        "render_end_state": "@C01_NADIA jaw set, eyes on @C02_ROMAN — decision point.",
    },
    "CLIP_SC0111_05": {
        "render_start_state": "@C01_NADIA closes distance — one step forward. Bilateral hold begins.",
        "render_end_state": "@C01_NADIA both thumbs on @C02_ROMAN's neck, sustained. @C02_ROMAN standing, hands on @C01_NADIA's forearms.",
    },
    "CLIP_SC0111_06": {
        "render_start_state": "@C01_NADIA maintaining bilateral hold. @C02_ROMAN still upright, grip weakening.",
        "render_end_state": "@C02_ROMAN on corridor floor. @C01_NADIA on one knee beside @C02_ROMAN, hold released.",
    },
    "CLIP_SC0111_07": {
        "render_start_state": "@C01_NADIA on one knee on corridor floor. @C02_ROMAN on floor beside her.",
        "render_end_state": "@C01_NADIA standing. @C02_ROMAN on corridor floor.",
    },
    "CLIP_SC0111_08": {
        "render_start_state": "@C01_NADIA standing. @C02_ROMAN on floor, chest moving.",
        "render_end_state": "@C01_NADIA moving toward corridor end. @C02_ROMAN on floor behind her.",
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

        # Update figure render fields for existing figures
        fig_render = rd.get("figure_render", {})
        for fig in shot.get("figures") or []:
            fid = fig.get("figure_id")
            if fid in fig_render:
                for k, v in fig_render[fid].items():
                    fig[k] = v

        # Add missing figures (SC0111 has no missing figures, but keep the pattern)
        add_figs = rd.get("add_figures", [])
        if add_figs:
            existing_aliases = {
                f.get("kling_alias") for f in (shot.get("figures") or [])
            }
            if "figures" not in shot or shot["figures"] is None:
                shot["figures"] = []
            for af in add_figs:
                if af.get("kling_alias") not in existing_aliases:
                    fid = af.get("figure_id")
                    merged = dict(af)
                    if fid in fig_render:
                        for k, v in fig_render[fid].items():
                            merged[k] = v
                    shot["figures"].append(merged)

    # Update notes and provenance
    data["notes"] = (
        "SC0111 v07 text-only literal pass (kling_literal_alias_locked): "
        "render_* fields authored for model-facing literal grammar; "
        "poetic prompt_action/lens_bias remain for human review only. "
        "Silent action scene — no dialogue; Format A throughout."
    )
    prov = data.get("provenance") or {}
    prov["render_fields_added_by"] = "claude_code (M5 v07 SC0111 literal pass)"
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
    print(f"=== SC0111 render_* field injection {'(DRY RUN) ' if DRY_RUN else ''}===")
    print(f"Found {len(clip_ids)} manifests.")
    for clip_id in clip_ids:
        inject_manifest(clip_id)
    print("Updating scene_continuity_ledger ...")
    update_ledger()
    print("Done.")


if __name__ == "__main__":
    main()
