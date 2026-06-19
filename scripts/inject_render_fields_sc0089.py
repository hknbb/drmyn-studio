"""inject_render_fields_sc0089.py

Add render_* fields (kling_literal_alias_locked) to SC0089 omni_clip_manifest files
and update the scene_continuity_ledger with render_start_state / render_end_state.

Also fixes legacy required_element_id references:
  LOC001 -> LOC005  (this scene is at LOC005 corridor, not LOC001 nursery)

Active aliases for SC0089:
  @C01_NADIA, @C06_ZARA, @LOC005_CORRIDOR
  C04 (Dimitri) is binding_status: planned — off-screen VO only, no alias in render_*.

Usage:
    python scripts/inject_render_fields_sc0089.py [--dry-run]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[1]
SCENE = "SC0089"
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
        if r == "LOC001":
            result.append("LOC005")
        else:
            result.append(r)
    return result


# ---------------------------------------------------------------------------
# Per-shot render data keyed by shot_id
# All text is kling_literal_alias_locked:
#   - alias-only (@C01_NADIA, @C06_ZARA, @LOC005_CORRIDOR)
#   - no role nouns (man/woman/protagonist/ally/operative)
#   - no metaphors / abstract language
#   - no bare "center/centered" as positional labels
#   - Dimitri (C04) is planned/off-screen — referenced as "comms-channel voice" only
# ---------------------------------------------------------------------------
SHOT_RENDER: dict[str, dict] = {
    # ------------------------------------------------------------------
    # CLIP 01 — establish corridor + Nadia and Zara moving
    # ------------------------------------------------------------------
    "SHOT_SC0089_01_A": {
        "render_action": (
            "@LOC005_CORRIDOR — concrete passage between sealed cargo facility (east wall) "
            "and drainage embankment (west wall). Overhead practical lights at intervals: "
            "each creates a tight pool on the ground; deep shadow lies between pools. "
            "No figures in frame. Left-to-right axis."
        ),
        "render_camera": "Wide static. Full sight-line along corridor. Pool-shadow-pool rhythm fills frame.",
        "render_diegetic_audio": "Low exterior wind. Distant cargo-facility hum. Concrete ambient.",
        # LOC001 -> LOC005 fix handled by fix_elem_ids
    },
    "SHOT_SC0089_01_B": {
        "render_action": (
            "@C01_NADIA moves left-to-right through shadow between second and third "
            "overhead pools. @C06_ZARA follows 8 meters behind, same pace, "
            "same distance from the west wall. Both arms low. No sprint."
        ),
        "render_camera": "Medium-wide tracking left. Both figures at 8m separation visible.",
        "render_diegetic_audio": "Footsteps on concrete at measured cadence. Night wind. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA walks left-to-right in shadow, arms low, controlled pace.",
                "render_label": "dark field jacket, close-fitted, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA follows @C01_NADIA 8 meters behind, same pace and wall distance.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 02 — Nadia stops, raises hold-position signal
    # ------------------------------------------------------------------
    "SHOT_SC0089_02_A": {
        "render_action": (
            "@C01_NADIA stops at edge of third overhead pool. "
            "@C01_NADIA's right arm rises — hand held up, fingers together, palm facing back. "
            "@C01_NADIA does not turn her head."
        ),
        "render_camera": "Medium-close static. @C01_NADIA at pool edge, raised hand visible.",
        "render_diegetic_audio": "Footsteps stop. Night wind holds. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA stops and raises right hand — palm back, fingers together.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 03 — Nadia scans corridor geometry ahead (silent)
    # ------------------------------------------------------------------
    "SHOT_SC0089_03_A": {
        "render_action": (
            "@C01_NADIA stands at pool edge, facing right (north). "
            "@C01_NADIA's head turns in small arcs — scanning: four overhead pools ahead, "
            "drainage embankment running west, cargo wall running east. "
            "@C01_NADIA does not speak and does not move her feet."
        ),
        "render_camera": "Medium static. @C01_NADIA slightly right-of-center. Corridor depth visible behind.",
        "render_diegetic_audio": "Night wind. Concrete ambient. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA stands still, head turns slowly scanning the corridor ahead.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 04 — Tactical exchange: two teams, comms ping
    # ------------------------------------------------------------------
    "SHOT_SC0089_04_A": {
        "render_action": (
            "@C01_NADIA turns head left toward @C06_ZARA. "
            "@C01_NADIA's lips move at minimum volume. @C01_NADIA's jaw stays flat — tactical report, no inflection. "
            "Both @C01_NADIA and @C06_ZARA are stationary at the pool edge."
        ),
        "render_camera": "Medium-close static. @C01_NADIA head turned left. Dim corridor behind.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA turns head left, lips move at minimum volume.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_04_B": {
        "render_action": (
            "@C06_ZARA turns head toward @C01_NADIA. @C06_ZARA's lips move at low volume. "
            "@C06_ZARA's face is in partial shadow at the pool edge."
        ),
        "render_camera": "Medium-close static, slight over-shoulder. @C06_ZARA dominant. @C01_NADIA foreground edge.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA turns head toward @C01_NADIA, lips move low.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_04_C": {
        "render_action": (
            "@C01_NADIA faces forward, eyes ahead. "
            "@C01_NADIA's lips move at minimum volume — delivering information without turning. "
            "Jaw tight. No hand gesture."
        ),
        "render_camera": "Medium-close static. @C01_NADIA direct. Dim corridor pool behind.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA faces forward, lips move at minimum volume, jaw tight.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 05 — Broadcast decoy confirmed
    # ------------------------------------------------------------------
    "SHOT_SC0089_05_A": {
        "render_action": (
            "@C06_ZARA stands still. @C06_ZARA's eyes shift. "
            "@C06_ZARA's lips move — two words at low volume. "
            "@C06_ZARA's expression stays flat as understanding registers."
        ),
        "render_camera": "Medium-close static. @C06_ZARA direct. Dim overhead pool.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA stands still, eyes shift, lips move briefly.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_05_B": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume. "
            "@C01_NADIA's eyes stay ahead — confirming without turning toward @C06_ZARA."
        ),
        "render_camera": "Medium-close static. @C01_NADIA in dim corridor light, eyes ahead.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA eyes ahead, lips move at minimum volume, not turning.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_05_C": {
        "render_action": (
            "@C06_ZARA stands still, eyes tracking middle distance. "
            "Jaw set. No movement. @C06_ZARA's gaze holds forward."
        ),
        "render_camera": "Medium-close static. @C06_ZARA face in dim overhead light.",
        "render_diegetic_audio": "Night wind. No voices.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA stands still, eyes tracking forward, jaw set.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_05_D": {
        "render_action": (
            "@C06_ZARA's lips move at low volume. "
            "@C06_ZARA does not turn head. Eyes still forward."
        ),
        "render_camera": "Medium-close static. @C06_ZARA in dim pool edge.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA lips move at low volume, eyes forward, head still.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 06 — Deployment count confirmed
    # ------------------------------------------------------------------
    "SHOT_SC0089_06_A": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume. "
            "@C01_NADIA's eyes hold forward. Flat delivery — no inflection."
        ),
        "render_camera": "Medium-close static. @C01_NADIA dim corridor light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume, eyes forward, flat.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_06_B": {
        "render_action": (
            "@C06_ZARA turns head slightly left. @C06_ZARA's lips move at low volume. "
            "@C06_ZARA waits — requesting the count."
        ),
        "render_camera": "Medium-close static. @C06_ZARA in dim corridor.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA turns head slightly toward @C01_NADIA, lips move low.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_06_C": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume, eyes tracking south. "
            "@C01_NADIA does not gesture. Jaw tight. Delivers count without turning."
        ),
        "render_camera": "Medium-close static. @C01_NADIA dim practical pool.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume, eyes tracking south, jaw tight.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 07 — Nadia runs coverage-gap geometry (silent)
    # ------------------------------------------------------------------
    "SHOT_SC0089_07_A": {
        "render_action": (
            "@C01_NADIA's gaze moves left — to the west embankment surface. "
            "Then right — along the corridor ahead to the junction. "
            "@C01_NADIA's eyes arc in small sweeps, measuring. "
            "@C01_NADIA holds position; no vocal output."
        ),
        "render_camera": "Medium-close static. @C01_NADIA facing right. West embankment dark fill on left.",
        "render_diegetic_audio": "Night wind. Concrete ambient. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA holds position, eyes arcing between embankment and junction.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 08 — Coverage window stated; commitment
    # ------------------------------------------------------------------
    "SHOT_SC0089_08_A": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume. "
            "@C01_NADIA's eyes are fixed forward — delivering operational timing, not looking at @C06_ZARA."
        ),
        "render_camera": "Medium-close static. @C01_NADIA dim corridor pool.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume, eyes forward, not turning.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_08_B": {
        "render_action": (
            "@C06_ZARA's lips move at low volume. @C06_ZARA's gaze is steady. "
            "@C06_ZARA does not look away — stating the alternative without asking."
        ),
        "render_camera": "Medium-close static. @C06_ZARA dim pool edge.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA lips move at low volume, gaze steady, not looking away.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_08_C": {
        "render_action": (
            "@C01_NADIA's lips move. Two words at minimum volume. "
            "@C01_NADIA does not turn. Eyes stay forward."
        ),
        "render_camera": "Medium-close static. @C01_NADIA direct, eyes ahead.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move briefly, eyes forward, not turning.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 09 — Movement resumes: pool-dark-pool
    # ------------------------------------------------------------------
    "SHOT_SC0089_09_A": {
        "render_action": (
            "@C01_NADIA steps left-to-right into the bright overhead pool. "
            "Pace controlled — not fast, not slow. Arms low. "
            "@C01_NADIA crosses the pool and enters shadow beyond."
        ),
        "render_camera": "Medium tracking left. @C01_NADIA dominant. Overhead pool isolates then releases.",
        "render_diegetic_audio": "Footsteps on concrete. Night wind.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA steps into pool left-to-right, arms low, controlled pace.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_09_B": {
        "render_action": (
            "@C06_ZARA enters pool 8 meters behind @C01_NADIA, left-to-right. "
            "@C01_NADIA leads in shadow ahead. Both cross pool-shadow-pool sequence. "
            "8-meter separation maintained."
        ),
        "render_camera": "Medium-wide tracking left. Both figures at separation in pool-dark-pool rhythm.",
        "render_diegetic_audio": "Footsteps on concrete. Overhead pool hum.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA enters pool behind @C01_NADIA, same pace, same wall distance.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
            "FIG_NADIA": {
                "render_action": "@C01_NADIA leads in shadow ahead of @C06_ZARA, controlled pace.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 10 — Comms pings from south; fifth light; repair seam
    # ------------------------------------------------------------------
    "SHOT_SC0089_10_A": {
        "render_action": (
            "@C01_NADIA and @C06_ZARA walk left-to-right at 8m separation, approaching the fifth pool. "
            "@C01_NADIA's head angle shifts slightly left — registering a sound from south."
        ),
        "render_camera": "Medium-wide tracking left. Both figures at interval in fifth-pool approach.",
        "render_diegetic_audio": "Footsteps on concrete. Brief comms ping from south — military cadence.",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "@C01_NADIA walks left-to-right, head angle shifts slightly south.",
                "render_label": "dark field jacket, night-transit build.",
            },
            {
                "figure_id": "FIG_ZARA",
                "base_element_id": "C06",
                "kling_alias": "@C06_ZARA",
                "role": "Zara, operative ally",
                "render_action": "@C06_ZARA follows 8 meters behind @C01_NADIA, controlled pace.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        ],
    },
    "SHOT_SC0089_10_B": {
        "render_action": (
            "@C01_NADIA continues walking left-to-right. @C01_NADIA's jaw shifts — registers the radio. "
            "No change in pace. Eyes hold ahead. Comms-channel voice from south on the command channel (off-screen)."
        ),
        "render_camera": "Medium-close tracking. @C01_NADIA dominant. Corridor moving behind.",
        "render_diegetic_audio": "[FORMAT A — no native voice for off-screen comms] Command-channel static, then voice, then silence.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA walks, jaw shifts registering the radio, pace unchanged, eyes ahead.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_10_C": {
        "render_action": (
            "@C01_NADIA and @C06_ZARA stop or slow at the fifth overhead pool. "
            "@C01_NADIA's gaze moves to the embankment surface: a repair-pour section, "
            "slightly lighter than the base concrete, runs at mid-height. "
            "@C01_NADIA does not yet move toward it."
        ),
        "render_camera": "Medium static. Both figures at fifth pool. West embankment surface visible, lighter seam at mid-height.",
        "render_diegetic_audio": "Night wind. Pool hum.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA stops, gaze moves to lighter repair-seam section on embankment.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA stops behind @C01_NADIA, holds position.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 11 — Nadia presses seam; detects team on other side
    # ------------------------------------------------------------------
    "SHOT_SC0089_11_A": {
        "render_action": (
            "@C01_NADIA presses two fingers against the lighter repair section of the west wall. "
            "@C01_NADIA holds still. @C01_NADIA's head tilts slightly toward the wall — listening."
        ),
        "render_camera": "Medium-close static. @C01_NADIA's hand on concrete wall surface. Tactile detail of seam texture.",
        "render_diegetic_audio": "No voices. Night ambient. Faint subterranean vibration implied.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA presses two fingers to embankment wall, holds still, head slightly angled toward wall.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_11_B": {
        "render_action": (
            "@C01_NADIA keeps fingers on the wall. @C01_NADIA's lips move at minimum volume. "
            "@C01_NADIA's eyes are angled down toward the seam — not toward @C06_ZARA."
        ),
        "render_camera": "Medium-close static. @C01_NADIA face and hand on wall, eyes down at seam.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA fingers on wall, lips move at minimum volume, eyes on seam.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 12 — Zara "How—" + Nadia explains; Zara looks to junction
    # ------------------------------------------------------------------
    "SHOT_SC0089_12_A": {
        "render_action": (
            "@C06_ZARA's mouth opens. @C01_NADIA's hand presses the seam once more — "
            "the answer delivered through touch before words. "
            "@C01_NADIA's lips move low, explaining. @C06_ZARA listens, still."
        ),
        "render_camera": "Medium-close static. @C01_NADIA hand on seam dominant. @C06_ZARA behind.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA's mouth opens, then closes, listening to @C01_NADIA.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
            "FIG_NADIA": {
                "render_action": "@C01_NADIA hand on seam, lips move at low volume explaining.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_12_B": {
        "render_action": (
            "@C06_ZARA turns head left-to-right (north). "
            "@C06_ZARA's gaze holds the junction 100 meters ahead. "
            "Drainage cut visible as a dark horizontal gap at the base of the embankment."
        ),
        "render_camera": "Medium-close static. @C06_ZARA right-of-frame. Junction depth behind.",
        "render_diegetic_audio": "Night wind. No voices.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA turns head north, gaze holds junction distance and drainage cut gap.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 13 — How many / one or two / advance element
    # ------------------------------------------------------------------
    "SHOT_SC0089_13_A": {
        "render_action": (
            "@C06_ZARA turns head toward @C01_NADIA. @C06_ZARA's lips move at minimum volume. "
            "No inflection — a formal question."
        ),
        "render_camera": "Medium-close static. @C06_ZARA bright pool light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA turns head to @C01_NADIA, lips move at minimum volume.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_13_B": {
        "render_action": (
            "@C01_NADIA's lips move. @C01_NADIA does not turn. Flat delivery."
        ),
        "render_camera": "Medium-close static. @C01_NADIA bright pool light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move briefly, eyes forward, flat delivery.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_13_C": {
        "render_action": (
            "@C06_ZARA's eyes shift right, then return forward. @C06_ZARA's lips move at low volume. "
            "@C06_ZARA absorbs the new threat geometry without visible agitation."
        ),
        "render_camera": "Medium-close static. @C06_ZARA direct, pool light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA eyes shift right then forward, lips move low.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 14 — Closing geometry (both figures, wide)
    # ------------------------------------------------------------------
    "SHOT_SC0089_14_A": {
        "render_action": (
            "@C01_NADIA faces north (right), stationary. @C06_ZARA holds position 8 meters south (left). "
            "The corridor behind them stretches south; the junction is ahead north. "
            "Both @C01_NADIA and @C06_ZARA are still."
        ),
        "render_camera": "Wide static. Both figures in corridor. Junction ahead (right). Open corridor behind (left).",
        "render_diegetic_audio": "Night wind. Distant comms ping from south.",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "@C01_NADIA faces north, stationary, not speaking.",
                "render_label": "dark field jacket, night-transit build.",
            },
            {
                "figure_id": "FIG_ZARA",
                "base_element_id": "C06",
                "kling_alias": "@C06_ZARA",
                "role": "Zara, operative ally",
                "render_action": "@C06_ZARA holds position 8 meters behind @C01_NADIA, still.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # CLIP 15 — Nadia's compressed decision; "We go through"
    # ------------------------------------------------------------------
    "SHOT_SC0089_15_A": {
        "render_action": (
            "@C01_NADIA's gaze moves: left to drainage cut shadow at embankment base, "
            "right south along the corridor. @C01_NADIA's eyes arc in small sweeps — "
            "seam, cut gap, south distance. @C01_NADIA does not move her feet."
        ),
        "render_camera": "Medium-close static. @C01_NADIA's eyes in motion. Corridor depth behind.",
        "render_diegetic_audio": "Night wind. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA gaze arcs between drainage cut, seam, and south distance.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_15_B": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume. @C01_NADIA's gaze holds forward. "
            "@C01_NADIA does not turn toward @C06_ZARA."
        ),
        "render_camera": "Medium-close static. @C01_NADIA direct, bright pool light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume, gaze forward, not turning.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 16 — Zara objects; Nadia states numbers, closes decision
    # ------------------------------------------------------------------
    "SHOT_SC0089_16_A": {
        "render_action": (
            "@C06_ZARA's mouth opens. @C01_NADIA's lips begin moving before @C06_ZARA finishes — "
            "cutting across with numbers at minimum volume. @C06_ZARA's mouth closes. "
            "@C01_NADIA delivers count and timing flat, then stops."
        ),
        "render_camera": "Medium-close static. @C01_NADIA slightly dominant. @C06_ZARA at side.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA mouth opens, then closes as @C01_NADIA cuts across.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume delivering count and timing, flat.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 17 — Silent exchange; Zara commits; tactical question
    # ------------------------------------------------------------------
    "SHOT_SC0089_17_A": {
        "render_action": (
            "@C01_NADIA and @C06_ZARA face each other. Both still. "
            "@C01_NADIA's gaze on @C06_ZARA's face; @C06_ZARA holds @C01_NADIA's gaze. "
            "No gesture. Neither turns."
        ),
        "render_camera": "Medium static. Both @C01_NADIA and @C06_ZARA in bright pool, equal frame weight.",
        "render_diegetic_audio": "Night wind. No voices.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA faces @C06_ZARA, still, gaze held on @C06_ZARA's face.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA faces @C01_NADIA, still, holds @C01_NADIA's gaze.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_17_B": {
        "render_action": (
            "@C06_ZARA's lips move at low volume. @C06_ZARA does not break eye contact with @C01_NADIA."
        ),
        "render_camera": "Medium-close static. @C06_ZARA direct. @C01_NADIA edge of frame.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA lips move low, eye contact with @C01_NADIA held.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 18 — Nadia "Over": climb + neutralize operative
    # ------------------------------------------------------------------
    "SHOT_SC0089_18_A": {
        "render_action": (
            "@C01_NADIA's lips move — one word at minimum volume. "
            "@C01_NADIA turns and approaches the west embankment wall. "
            "@C01_NADIA reaches for a pipe bracket at 2m height. "
            "@C01_NADIA climbs — right hand then left foot, practiced sequence — "
            "and goes flat at the top rim. @C06_ZARA stays at base."
        ),
        "render_camera": "Medium-wide tracking. @C01_NADIA approaches wall, climbs, tops out. @C06_ZARA at base.",
        "render_diegetic_audio": "[FORMAT A — no native voice for 'Over'] Concrete scrape of climb. Night wind.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move briefly, turns to wall, grabs bracket, climbs, goes flat at rim.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    "SHOT_SC0089_18_B": {
        "render_action": (
            "@C01_NADIA drops from embankment rim. @C01_NADIA lands controlled — weight forward, arms wrap. "
            "An unseen figure on the far side goes down. @C01_NADIA straightens."
        ),
        "render_camera": "Medium handheld. @C01_NADIA descending and neutralizing unseen figure.",
        "render_diegetic_audio": "Impact on ground. Then silence.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA drops from rim, lands controlled, arms wrap, figure goes down, straightens.",
                "render_label": "dark field jacket, night-transit build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 19 — Zara climbs; lands wrong; Nadia at her side
    # ------------------------------------------------------------------
    "SHOT_SC0089_19_A": {
        "render_action": (
            "@C01_NADIA's hand rises above embankment rim — upward signal. "
            "@C06_ZARA grips the bracket and climbs. @C06_ZARA reaches the top and descends the far side. "
            "@C06_ZARA's landing is weight-distributed but @C06_ZARA drops to one knee."
        ),
        "render_camera": "Medium tracking. @C06_ZARA climbing and landing. @C01_NADIA in foreground at base.",
        "render_diegetic_audio": "Climb scrape. Weight landing on concrete.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA raises hand above rim signaling up, then watches @C06_ZARA.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA climbs, descends far side, lands — drops to one knee.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_19_B": {
        "render_action": (
            "@C01_NADIA moves to @C06_ZARA — four steps, crouches. "
            "@C01_NADIA's hand moves toward @C06_ZARA's left side. "
            "@C01_NADIA's lips move at minimum volume."
        ),
        "render_camera": "Medium-close handheld. @C01_NADIA crouching beside @C06_ZARA.",
        "render_diegetic_audio": "[FORMAT A — no native voice for 'Where'] Controlled breathing. No footsteps.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA crouches beside @C06_ZARA, hand toward @C06_ZARA's left side, lips move low.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA on one knee, controlled, not falling.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 20 — Zara reports wound
    # ------------------------------------------------------------------
    "SHOT_SC0089_20_A": {
        "render_action": (
            "@C06_ZARA's mouth moves. @C06_ZARA stops mid-sentence. @C06_ZARA breathes — controlled. "
            "@C06_ZARA's right hand goes to @C06_ZARA's left side below the jacket. "
            "Hand pulls back; the dark is darker. @C06_ZARA's eyes hold @C01_NADIA."
        ),
        "render_camera": "Medium-close handheld. @C06_ZARA dominant. @C01_NADIA edge-of-frame.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Controlled breath. Night ambient.",
        "figure_render": {
            "FIG_ZARA": {
                "render_action": "@C06_ZARA mouth moves, stops, breathes, right hand to left side below jacket, pulls back, eyes on @C01_NADIA.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 21 — Nadia assesses wound; "Can you move" / "Yes"
    # ------------------------------------------------------------------
    "SHOT_SC0089_21_A": {
        "render_action": (
            "@C01_NADIA crouches beside @C06_ZARA. @C01_NADIA looks at @C06_ZARA's left side, "
            "then at @C06_ZARA's face. @C01_NADIA does not touch. @C06_ZARA holds position. Both still."
        ),
        "render_camera": "Medium-close static. @C01_NADIA and @C06_ZARA close together. Corridor behind.",
        "render_diegetic_audio": "Controlled breathing. Night wind.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA crouches, looks at @C06_ZARA's side, then face, does not touch.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA holds position, still, controlled.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_21_B": {
        "render_action": (
            "@C01_NADIA's lips move at minimum volume. @C06_ZARA's lips move — one syllable. "
            "@C06_ZARA does not look away from @C01_NADIA."
        ),
        "render_camera": "Medium-close static. Both faces in dim light.",
        "render_diegetic_audio": "[FORMAT A — no native voice] Night ambient.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA lips move at minimum volume, watching @C06_ZARA.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA lips move — one syllable. Does not look away from @C01_NADIA.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    # ------------------------------------------------------------------
    # CLIP 22 — Moving together; drainage cut revealed
    # ------------------------------------------------------------------
    "SHOT_SC0089_22_A": {
        "render_action": (
            "@C01_NADIA's left shoulder moves under @C06_ZARA's right arm. "
            "Both move left-to-right at controlled pace — @C01_NADIA bearing partial weight. "
            "@C06_ZARA does not lean more than geometry requires."
        ),
        "render_camera": "Medium tracking left. Both figures moving together. @C01_NADIA bearing load.",
        "render_diegetic_audio": "[FORMAT A — no native voice for 'Then we move now'] Footsteps on concrete. Controlled breathing.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA's left shoulder under @C06_ZARA's right arm, both moving left-to-right.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA's right arm over @C01_NADIA's shoulder, moving, weight controlled.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
    "SHOT_SC0089_22_B": {
        "render_action": (
            "@LOC005_CORRIDOR drainage conduit entrance at embankment base — "
            "1 meter wide, concrete grime and calcite streaks, dark interior. No figures in frame."
        ),
        "render_camera": "Wide static, low angle. Conduit opening at base of embankment. Darkness inside.",
        "render_diegetic_audio": "Night wind. No voices.",
        # LOC001 -> LOC005 fix handled by fix_elem_ids
    },
    # ------------------------------------------------------------------
    # CLIP 23 — At the cut; cover pulled; they go in
    # ------------------------------------------------------------------
    "SHOT_SC0089_23_A": {
        "render_action": (
            "@C01_NADIA and @C06_ZARA reach the conduit entrance, slowing. "
            "@C01_NADIA looks back (left, south) over shoulder. "
            "@C06_ZARA's right hand holds @C06_ZARA's left side. "
            "Multiple comms pings audible from south."
        ),
        "render_camera": "Medium-wide tracking then static. Both figures at conduit. Corridor behind shows empty.",
        "render_diegetic_audio": "Multiple comms pings from south in quick succession. Night ambient.",
        "add_figures": [
            {
                "figure_id": "FIG_NADIA",
                "base_element_id": "C01",
                "kling_alias": "@C01_NADIA",
                "role": "Nadia, the protagonist",
                "render_action": "@C01_NADIA at conduit entrance, looks back south over shoulder.",
                "render_label": "dark field jacket, night-transit build.",
            },
            {
                "figure_id": "FIG_ZARA",
                "base_element_id": "C06",
                "kling_alias": "@C06_ZARA",
                "role": "Zara, operative ally",
                "render_action": "@C06_ZARA at conduit entrance, right hand holding left side.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        ],
    },
    "SHOT_SC0089_23_B": {
        "render_action": (
            "@C01_NADIA grips the drain cover — heavy, circular. @C01_NADIA pulls with both hands, "
            "torso engaged. The cover shifts. @C01_NADIA and @C06_ZARA move into the conduit opening."
        ),
        "render_camera": "Medium handheld, low angle. @C01_NADIA at cover. @C06_ZARA entering.",
        "render_diegetic_audio": "Metal scrape on concrete. Footsteps entering conduit.",
        "figure_render": {
            "FIG_NADIA": {
                "render_action": "@C01_NADIA grips drain cover with both hands, pulls, torso engaged — cover shifts.",
                "render_label": "dark field jacket, night-transit build.",
            },
            "FIG_ZARA": {
                "render_action": "@C06_ZARA moves into conduit opening behind @C01_NADIA.",
                "render_label": "khaki-olive jacket, field-night build.",
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Continuity ledger render states (alias-locked, no role nouns, no bare center)
# ---------------------------------------------------------------------------
LEDGER_RENDER: dict[str, dict] = {
    "CLIP_SC0089_01": {
        "render_start_state": "@LOC005_CORRIDOR — overhead pools at intervals, deep shadow between. No figures in frame.",
        "render_end_state": "@C01_NADIA in shadow between pools moving left-to-right. @C06_ZARA 8 meters behind, same axis.",
    },
    "CLIP_SC0089_02": {
        "render_start_state": "@C01_NADIA and @C06_ZARA moving left-to-right in shadow.",
        "render_end_state": "@C01_NADIA stationary at pool edge, right hand raised (stop signal). @C06_ZARA position held behind.",
    },
    "CLIP_SC0089_03": {
        "render_start_state": "@C01_NADIA at pool edge, right hand raised. @C06_ZARA behind, stationary.",
        "render_end_state": "@C01_NADIA holding position, gaze tracking corridor geometry ahead. @C06_ZARA behind, stationary.",
    },
    "CLIP_SC0089_04": {
        "render_start_state": "@C01_NADIA turns toward @C06_ZARA — tactical exchange begins.",
        "render_end_state": "@C01_NADIA delivered comms-ping spacing analysis. Both stationary.",
    },
    "CLIP_SC0089_05": {
        "render_start_state": "@C06_ZARA receiving explanation. @C01_NADIA facing forward.",
        "render_end_state": "@C06_ZARA confirmed eastern deployment axis. Both stationary.",
    },
    "CLIP_SC0089_06": {
        "render_start_state": "@C01_NADIA confirming second deployment axis. Both stationary.",
        "render_end_state": "@C01_NADIA delivered threat count — at least eight from south junction. Both stationary.",
    },
    "CLIP_SC0089_07": {
        "render_start_state": "@C01_NADIA facing forward, running coverage-gap geometry. @C06_ZARA behind, stationary.",
        "render_end_state": "@C01_NADIA holding position, gap calculation complete. Silent.",
    },
    "CLIP_SC0089_08": {
        "render_start_state": "@C01_NADIA stating coverage-gap timing to @C06_ZARA.",
        "render_end_state": "@C01_NADIA declared intent: committed. Both stationary.",
    },
    "CLIP_SC0089_09": {
        "render_start_state": "@C01_NADIA begins controlled movement into third light pool. @C06_ZARA follows.",
        "render_end_state": "Both @C01_NADIA and @C06_ZARA moving left-to-right through pool-dark-pool sequence.",
    },
    "CLIP_SC0089_10": {
        "render_start_state": "Both @C01_NADIA and @C06_ZARA moving left-to-right, approaching fifth pool. Comms pings from south.",
        "render_end_state": "Both @C01_NADIA and @C06_ZARA at fifth pool, stationary. Embankment repair seam visible.",
    },
    "CLIP_SC0089_11": {
        "render_start_state": "@C01_NADIA stops, presses fingers to repair seam. @C06_ZARA holds behind.",
        "render_end_state": "@C01_NADIA fingers on seam, alerted @C06_ZARA: team on far side.",
    },
    "CLIP_SC0089_12": {
        "render_start_state": "@C06_ZARA beginning to ask; @C01_NADIA explaining seam vibration.",
        "render_end_state": "@C06_ZARA looking north to junction — drainage cut shadow visible 100m ahead.",
    },
    "CLIP_SC0089_13": {
        "render_start_state": "@C06_ZARA asking for count. @C01_NADIA responding.",
        "render_end_state": "@C06_ZARA confirmed advance element came around. Both stationary.",
    },
    "CLIP_SC0089_14": {
        "render_start_state": "Both @C01_NADIA and @C06_ZARA stationary. Advance element ahead; main force south.",
        "render_end_state": "Both still. @C01_NADIA computing least-bad move.",
    },
    "CLIP_SC0089_15": {
        "render_start_state": "@C01_NADIA's gaze moving across seam, cut gap, south distance — running decision.",
        "render_end_state": "@C01_NADIA declared decision: go through.",
    },
    "CLIP_SC0089_16": {
        "render_start_state": "@C06_ZARA beginning to object. @C01_NADIA cutting across with numbers.",
        "render_end_state": "@C01_NADIA completed restatement — numbers, timing, decision closed. Both stationary.",
    },
    "CLIP_SC0089_17": {
        "render_start_state": "Both @C01_NADIA and @C06_ZARA facing each other — silent exchange.",
        "render_end_state": "@C06_ZARA asked tactical question: through seam or over.",
    },
    "CLIP_SC0089_18": {
        "render_start_state": "@C01_NADIA declared: over. Moving to west embankment wall to climb.",
        "render_end_state": "@C01_NADIA on far side of embankment. Advance operative neutralized.",
    },
    "CLIP_SC0089_19": {
        "render_start_state": "@C01_NADIA signaled up. @C06_ZARA climbing embankment.",
        "render_end_state": "@C06_ZARA on one knee on far side. @C01_NADIA moving to @C06_ZARA.",
    },
    "CLIP_SC0089_20": {
        "render_start_state": "@C06_ZARA reporting wound location. Hand pulled back from left side below jacket.",
        "render_end_state": "@C06_ZARA finished wound report. Both stationary.",
    },
    "CLIP_SC0089_21": {
        "render_start_state": "@C01_NADIA assessing @C06_ZARA's wound silently.",
        "render_end_state": "@C06_ZARA confirmed: can move. Both preparing to continue.",
    },
    "CLIP_SC0089_22": {
        "render_start_state": "@C01_NADIA's shoulder under @C06_ZARA's arm. Both moving left-to-right toward drainage cut.",
        "render_end_state": "Drainage cut entrance visible — @LOC005_CORRIDOR conduit opening at embankment base.",
    },
    "CLIP_SC0089_23": {
        "render_start_state": "Both @C01_NADIA and @C06_ZARA at drainage cut entrance. Comms pinging from south.",
        "render_end_state": "@C01_NADIA and @C06_ZARA inside conduit. Cover pulled shut.",
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

        # Update figure render fields for existing figures
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
        "SC0089 v07 text-only literal pass (kling_literal_alias_locked): "
        "render_* fields authored for model-facing literal grammar; "
        "poetic prompt_action/lens_bias remain for human review only. "
        "Legacy element ID refs fixed: LOC001→LOC005."
    )
    prov = data.get("provenance") or {}
    prov["render_fields_added_by"] = "claude_code (M5 v07 SC0089 literal pass)"
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
    print(f"=== SC0089 render_* field injection {'(DRY RUN) ' if DRY_RUN else ''}===")
    print(f"Found {len(clip_ids)} manifests.")
    for clip_id in clip_ids:
        inject_manifest(clip_id)
    print("Updating scene_continuity_ledger ...")
    update_ledger()
    print("Done.")


if __name__ == "__main__":
    main()
