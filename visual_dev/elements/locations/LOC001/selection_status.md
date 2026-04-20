# LOC001 — Vale Residence, Vardova — Image Selection Status

**Status: BLOCKED — no source images collected**

## What Is Needed

Three distinct sub-area image groups. Do not conflate their visual registers.

### Sub-Area 1: Kitchen Passage / East-Wing Corridor
- **Pilot scene:** SC0001 (early morning)
- **Target path:** `sub_areas/kitchen_passage/`
- **Visual register:** Pale stone, filtered early daylight, surveillance geometry
- **Key props in frame:** PROP003 (tilted photo frame — misalignment and dust-shadow are critical), folded linens
- **Image status:** Not collected

### Sub-Area 2: Jin's Room / Nursery
- **Pilot scene:** SC0003 (mid-morning)
- **Target path:** `sub_areas/jins_room/`
- **Visual register:** Warm tones, filtered morning light, closed curtains, crib, white-noise machine
- **Key props in frame:** PROP001 context (bracelet with Nadia present)
- **Image status:** Not collected
- **Note:** This sub-area is distinctly warmer and more intimate than the corridor; do not apply corridor palette

### Sub-Area 3: Roman's Trophy Room
- **Pilot scene:** SC0009 (night)
- **Target path:** `sub_areas/trophy_room/`
- **Visual register:** Curated darkness, glass cases, shelf objects, hard-controlled night tones
- **Register note:** System-recalibration, not grief or overt loss; no gothic theatrics
- **Image status:** Not collected

## Grounding

See `source_notes.md` and `planning/locations/LOC001.yaml` for full architectural and lighting profile.

## Copyright / Provenance

Pending. No images selected or sourced for any sub-area.

## Next Steps

1. Create sub-area subdirectory stubs (`sub_areas/kitchen_passage/`, `sub_areas/jins_room/`, `sub_areas/trophy_room/`) before committing images
2. Source candidate reference images per sub-area separately
3. Confirm copyright/provenance clearance per image
4. Commit as `.png` / `.jpg` / `.jpeg` / `.webp` — LFS tracking is automatic at any depth (PR4B)
5. Update `pack_manifest.yaml` on seeding, noting which sub-areas are populated
