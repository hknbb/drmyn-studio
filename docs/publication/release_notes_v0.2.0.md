# Release Notes — v0.2.0 (Film Aesthetic Bible)

**Release date:** 2026-05-04
**Branch history:** AB-1 (PR #24) → AB-2 (PR #25) → AB-3 (PR #26) → AB-4 (this PR)

---

## Summary

v0.2.0 introduces the **Film Aesthetic Bible** system: a machine-readable registry of named visual mood-board packs that injects deterministic, scene-grounded keywords into every T2I prompt without web fetches, random selection, or lifecycle promotion.

---

## Changes by batch

### AB-1 — Aesthetic Bible schema, registry, validator (PR #24)

**New files:**
- `schemas/aesthetic_bible.schema.json` — JSON Schema draft 2020-12, `additionalProperties: false`
- `planning/aesthetic_bible.yaml` — 4 starter packs derived from `source/style_bible.md`
- `scripts/agents/aesthetic_bible.py` — pack loader + deterministic resolver helpers
- `docs/publication/aesthetic_bible_overview.md` — pack rationale for reviewers
- `tests/test_aesthetic_bible.py` — schema + helper + validator dispatch tests

**Modified files:**
- `scripts/validate_production_records.py` — `aesthetic_bible` record type dispatch added

**Starter packs and their style bible origins:**

| Pack ID | Visual territory | Style bible sections |
|---|---|---|
| `VALE_DOMESTIC_RESTRAINT` | Vale residence — pale stone, threshold geometry | Palette rules, Interior rules, Framing rules |
| `KASPAR_INSTITUTIONAL_SURVEILLANCE` | Kaspar Terminal — functional whites, monitor glow | Camera behavior rules, Lighting rules |
| `MERIN_INDUSTRIAL_DECAY` | MERIN waterfront — grey-orange haze, salt/diesel | Exterior rules, Texture rules |
| `ORACLE_BROADCAST_CLEAN` | Oracle Prime broadcast — high-contrast typographic | Broadcast-world vs lived-world |

### AB-2 — Schema hooks + agent injection (PR #25)

**Schema changes** (all fields optional — backward compatible):
- `schemas/scene_card.schema.json` — `visual_targets.aesthetic_pack_refs`
- `schemas/character_sheet.schema.json` — top-level `aesthetic_pack_refs`
- `schemas/location_sheet.schema.json` — top-level `aesthetic_pack_refs`
- `schemas/wardrobe_record.schema.json` — top-level `aesthetic_pack_refs`
- `schemas/prop_record.schema.json` — top-level `aesthetic_pack_refs`
- `schemas/prompt_record.schema.json` — `source_refs.aesthetic_refs`
- `schemas/storyboard_option.schema.json` — option-level `aesthetic_pack_refs`

**Agent changes:**
- `scripts/agents/source_context.py` — loads aesthetic bible; missing file tolerant
- `scripts/agents/neutral_brief.py` — resolves keywords + negatives per element; unknown pack refs warn without inventing data
- `scripts/agents/adapters/_base.py` — writes `source_refs.aesthetic_refs` and `generation_params.aesthetic_keywords_injected`
- `scripts/agents/adapters/midjourney.py` — compact comma-tail within ≤80 word budget
- `scripts/agents/adapters/chatgpt_image.py` — `"Visual world: …"` natural-language phrase
- `scripts/agents/adapters/nano_banana.py` — `"World consistency: …"` identity anchor
- `scripts/agents/storyboard_options.py` — propagates `aesthetic_pack_refs` to each option

**Tests:** `tests/test_aesthetic_injection.py` (25 tests)

### AB-3 — SC0001 pilot migration (PR #26)

- `planning/scenes/SC0001/scene_card.yaml` — `visual_targets.aesthetic_pack_refs: [VALE_DOMESTIC_RESTRAINT]` added
- `visual_dev/storyboards/SC0001/storyboard_options.yaml` — 5 candidate options generated, all carrying `VALE_DOMESTIC_RESTRAINT`; `selected_option: null` (human selection pending)
- `tests/test_sc0001_aesthetic_migration.py` — 6 migration tests

Pre-check confirmed no prior generated files existed; no approved/locked records deleted.

### AB-4 — Release metadata (this PR)

- `CITATION.cff` — version 0.2.0; `doi:` field removed (real DOI added in mini-PR after Zenodo processes)
- `.zenodo.json` — version 0.2.0; description and keywords updated
- `README.md` — Film Aesthetic Bible section added
- `docs/publication/release_notes_v0.2.0.md` — this file

---

## Backward compatibility

All new schema fields are optional. Existing records without `aesthetic_pack_refs` or `aesthetic_refs` continue to validate without modification.

## Invariants preserved

- No web fetches — aesthetic bible provides offline keyword lists for human curator searches
- No lifecycle promotion — `selected_option`, `approved`, `canon_lock`, `locked` states untouched
- No generated media — metadata-only pipeline unchanged
- No DOI placeholder — `doi:` field removed; real DOI mini-PR follows Zenodo publication

## Test suite

```
385 passed (AB-3 state)
Production validator: 4 valid, 0 invalid
```

---

## Next steps after release

1. Create GitHub release `v0.2.0` on `drmyn-studio-public` — human action
2. Zenodo auto-captures release and generates DOI
3. Mini-PR: add real DOI to `CITATION.cff` and update README badge URL if needed
4. SC0001 storyboard option selection — human decision, separate workflow
