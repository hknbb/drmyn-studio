# Stage B PR1 — Schema Groundwork Note

**Date:** 2026-04-19
**Scope:** Additive schema changes only. No folder scaffolding, no scene card data migration, no Omni pipeline activation.

---

## What Was Added

### New Schemas (B1)

| File | Purpose |
|---|---|
| `schemas/element_set_record.schema.json` | Curated element set records per scene, used as input context for Omni generation runs |
| `schemas/omni_generation_record.schema.json` | Reproducible provenance record for a single Omni generation run |
| `schemas/lipsync_record.schema.json` | Post-dialogue lipsync record for one shot or scene segment |

### Expanded Enums (B2)

`schemas/prompt_record.schema.json` — `prompt_type` enum expanded from 8 to 17 values. Nine values added:
`t2i_character_element`, `t2i_location_element`, `t2i_prop_element`, `t2i_style_reference`,
`omni_instruction`, `lipsync_audio`, `lipsync_shot`, `color_lut`, `sfx_design`.
All existing 8 values preserved unchanged.

### Additive Fields — Scene Card (B3)

`schemas/scene_card.schema.json` — 4 optional fields added to `properties` (not to `required`):
- `omni_set_ref` — reference to the element set for this scene's Omni generation
- `element_slot_allocation` — slot budget metadata object
- `shot_list_omni` — array of Omni shot plan objects
- `lipsync_plan` — lipsync planning metadata object

### Additive Fields — Sheet Schemas (B4)

All 3 fields optional, added to `properties` only.

**`schemas/character_sheet.schema.json`:**
- `kling_element_id`, `canonical_pack_path`, `voice_clone_ref`

**`schemas/location_sheet.schema.json`:**
- `kling_element_id`, `canonical_pack_path`, `lighting_variants`

**`schemas/prop_record.schema.json`:**
- `kling_element_id`, `canonical_pack_path`, `composite_refs`

---

## Backward Compatibility

All changes are strictly additive. No field was removed or made required. All existing validated records remain valid against the updated schemas. The Stage A closure audit and Phase 1 validator are unaffected.

---

## What PR1 Does NOT Include

- No Omni/element-set folder scaffolding (that is PR2)
- No scene card JSON data updates to populate the new fields (that is PR3)
- No 120-scene contract changes
- No screenplay mutations

---

## Next Steps

- **PR2:** Folder scaffolding for element sets and generation records under `visual_dev/` and `production/`
- **PR3:** Scene card field population for pilot scenes (SC0001, SC0003, SC0006, SC0008, SC0009)
