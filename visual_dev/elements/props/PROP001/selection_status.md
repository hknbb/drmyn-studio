# PROP001 — Jin's Medical Bracelet — Image Selection Status

**Status: HARD GATE — color decision must be resolved before any image is selected**

## The Gate

Source evidence supports **white** or **pale blue/white** appearance under changing light.
The planning record (`planning/props/PROP001.yaml`) flags this as an open `TODO_REVIEW`.

**Any reference image committed here becomes the color ground truth for all future appearances:**
SC0003, SC0010, SC0011, SC0014, SC0108, SC0109.

Committing the wrong color creates a continuity error across six scenes. **Do not select
or commit any reference image until a human reviewer has resolved this in planning.**

## What Is Needed (After Gate Clears)

| Item | Requirement |
|---|---|
| Form | Thin hospital-style plastic bracelet with printed ID strip |
| Color | As resolved by planning review |
| Clasp | Legible — Nadia adjusts it repeatedly |
| Lighting | Neutral; avoid color-casting that would obscure the resolved color |
| Style | Plain, medically plausible; not jewellery, not tech-futuristic |

## Continuity Importance

**High.** This prop recurs in SC0003, SC0010, SC0011, SC0014, SC0108, SC0109.
The reference image locked here governs all subsequent appearances.

## Copyright / Provenance

Pending. No images selected or sourced.

## Next Steps

1. **Resolve white vs pale blue/white in `planning/props/PROP001.yaml`** — human reviewer required
2. Source candidate reference images matching the resolved color
3. Photograph in neutral light
4. Confirm copyright/provenance clearance
5. Commit as `.png` / `.jpg` / `.jpeg` / `.webp` — LFS tracking is automatic (PR4B)
6. Update `pack_manifest.yaml` on seeding; note color decision was resolved and by whom
