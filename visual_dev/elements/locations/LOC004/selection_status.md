# LOC004 — Hidden Room / Anonymous Room — Image Selection Status

**Status: BLOCKED — no source images collected**

## What Is Needed

Two context-separated image groups (do not assert they are the same physical room):

| Group | Pilot scenes | Time | Key visual |
|---|---|---|---|
| `late_night/` | SC0008 (SC0009 carry-over) | Late night | Muted rented-room neutrals, city-night softness, bed/table/window/curtain |
| `afternoon/` | SC0004 (non-pilot) | Afternoon | Same geometry, practical window light |

**Priority:** `late_night/` group for pilot seeding (SC0008).

## Grounding

See `source_notes.md` and `planning/locations/LOC004.yaml` for spatial motifs and stable visual rules.

Key constraints:
- Room must read as anonymous, temporary, and unowned — not a noir hideout
- Intimacy comes from posture and withholding, not romantic set dressing
- Do not claim the two groups are the same room without source evidence

## Unresolved (Block Shared-Image Assumptions)

The identity of LOC004 as a single room vs a planning bucket of related rooms is explicitly
unresolved. Commit images under scene-context subfolders (`late_night/`, `afternoon/`) rather
than at the root of this pack, to preserve that ambiguity in the visual record.

## Copyright / Provenance

Pending. No images selected or sourced.

## Next Steps

1. Prioritize `late_night/` context for pilot (SC0008)
2. Source candidate reference images; keep them generic and anonymous
3. Confirm copyright/provenance clearance
4. Commit as `.png` / `.jpg` / `.jpeg` / `.webp` — LFS tracking is automatic (PR4B)
5. Update `pack_manifest.yaml` on seeding
