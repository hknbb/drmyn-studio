# Film Aesthetic Bible — Reviewer Overview

**Status:** Introduced in AB-1 (additive only). No prompt-generation behavior changes in this batch; downstream wiring lands in AB-2.

## What this is

`planning/aesthetic_bible.yaml` is a machine-readable registry of named
mood-board packs that capture the visual language of the film's distinct
narrative zones. It is a structured companion to the prose canonical
ruleset in [`source/style_bible.md`](../../source/style_bible.md), not a
replacement for it.

Each pack defines:

| Field | Purpose |
|---|---|
| `pack_id` | Stable `^[A-Z][A-Z0-9_]+$` identifier referenced from scene cards and element records |
| `name` | Human-readable label |
| `visual_thesis` | One-paragraph statement of what the pack means visually |
| `derived_from.style_bible_sections` | Section headings in `source/style_bible.md` that authorize this pack |
| `derived_from.scene_evidence` | Optional pointers to scene_card fields the pack draws on |
| `search_keywords` | Curator-facing search terms for manual reference gathering (Pinterest, image search). 8–30 entries |
| `element_keyword_map` | Per-element-type keyword shortlist (2–4 entries each) used by adapters in AB-2 to deterministically augment prompts |
| `do_not_keywords` | Negative constraints merged into prompt `negative_prompt` lists in AB-2 |

## Why it exists

Before AB-1, the only shared aesthetic input to prompt generation was the
prose `style_bible.md`, parsed solely for its "Do not do:" bullets to
build negative constraints. Positive visual vocabulary lived only in
per-element records and per-scene `visual_targets`, with no shared layer
ensuring that characters, locations, props, and wardrobe rendered for
the same narrative zone read as the same cinematic universe.

The aesthetic bible introduces that shared layer as schema-validated,
reviewable data — not as opaque prose, not as agent-discovered web
research.

## Initial packs (v1)

| Pack | Narrative zone |
|---|---|
| `VALE_DOMESTIC_RESTRAINT` | Vale residence: pale stone, controlled underuse, threshold geometry |
| `KASPAR_INSTITUTIONAL_SURVEILLANCE` | Kaspar Terminal & Veltain service zones: functional whites, steel, monitor glow |
| `MERIN_INDUSTRIAL_DECAY` | MERIN waterfront, Zoral corridor: weathered industrial realism |
| `ORACLE_BROADCAST_CLEAN` | Oracle Prime broadcast layer: calibrated false-clean, profit-machine register |

## Determinism guarantees

The helper module `scripts/agents/aesthetic_bible.py` exposes:

- `load_aesthetic_bible(repo_root)` — returns `None` if the file is
  absent (so scenes without aesthetic refs continue to build cleanly).
- `get_pack_ids_from_records(scene_card, element_record)` — ordered
  union (scene refs first, then element refs), deduplicated by first
  occurrence.
- `resolve_pack_keywords(packs, pack_ids, prompt_type, limit_per_pack=2)`
  — for each pack in order, take the first `limit_per_pack` entries of
  `element_keyword_map[prompt_type]`, then dedupe preserving order.
- `resolve_pack_negatives(packs, pack_ids)` — ordered union of
  `do_not_keywords` across the requested packs.

All resolvers use ordered `dict.fromkeys` deduplication; no random
sampling, no set-based ordering. The same inputs always produce the
same outputs across runs.

## Out of scope for AB-1

The following are explicitly deferred to later batches and **must not**
be inferred from AB-1:

- Schema fields on `scene_card`, `character_sheet`, `location_sheet`,
  `wardrobe_record`, `prop_record`, `prompt_record`, or
  `storyboard_option` to declare or consume aesthetic refs (AB-2).
- Agent integration (`SourceContext`, `NeutralBrief`, model adapters)
  (AB-2).
- SC0001 migration to a specific pack (AB-3).
- v0.2.0 release metadata, Zenodo DOI (AB-4).

AB-1 only adds the registry, the schema, the deterministic resolver, the
validator dispatch, the tests, and this document. Existing prompt-record
output is unchanged; existing tests continue to pass.

## Hard boundaries

- Agents do not fetch from the network. The `search_keywords` field is
  for the human curator to use in external tools (Pinterest, image
  search, model UI). Any future research-driven snapshot would land in
  a separate evidence record type, not here.
- No lifecycle promotion. The aesthetic bible never sets `pack_status`,
  `canon_lock`, `approved`, or `locked` on any record.
- No generated media. The registry is metadata only.

## Validator behavior

`scripts/validate_production_records.py` now scans
`planning/aesthetic_bible.yaml` as a singleton record of type
`aesthetic_bible` and validates it with
`schemas/aesthetic_bible.schema.json`. If the file is absent, the
validator emits zero issues for this record type (consistent with the
treatment of every other optional production-metadata directory).
