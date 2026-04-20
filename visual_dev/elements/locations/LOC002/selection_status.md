# LOC002 — Nadia's Private Study, Vale Residence — Image Selection Status

**Status: BLOCKED — no source images collected**

## What Is Needed

Night-interior reference images showing the room as an operational diagram:

| Element | Requirement |
|---|---|
| Desk | Central; reading/writing position; low-key practical light |
| North-wall vent grille | Must be architecturally plausible; do not show surveillance device in detail |
| Bookshelf | Background reference mass; no ornate styling |
| Corridor door | Present in frame logic for sightline geometry |
| Courtyard window | Present at sightline edge; night exterior |

## PROP006 Context (Resolved at Planning Layer)

PROP006 (vent-grille surveillance device) now has a planning record (`planning/props/PROP006.yaml`,
added Stage B PR4D). The original BLOCKER in `pack_manifest.yaml` is resolved at the planning layer.

**What this means for LOC002 images:**
- The vent grille area should be visually plausible for concealment of a small lens — do not over-engineer
- The device reads as a wire and a lens edge only; images of the room should not make it conspicuous
- LOC002 reference images are location references, not PROP006 images; do not conflate them

## Grounding

See `source_notes.md` and `planning/locations/LOC002.yaml` for spatial motifs and stable visual rules.

Night register only — no daylight variant is source-grounded in pilot evidence.

## Copyright / Provenance

Pending. No images selected or sourced.

## Next Steps

1. Source candidate night-interior reference images showing desk / vent / window geometry
2. Confirm copyright/provenance clearance
3. Commit as `.png` / `.jpg` / `.jpeg` / `.webp` — LFS tracking is automatic (PR4B)
4. Update `pack_manifest.yaml` on seeding, noting PROP006 blocker is planning-resolved
