# Stage A Closure Summary

Date: `2026-04-19`

This document records what Stage A was meant to accomplish, what is now complete, what
remains manual or outside-repo, and why the repo is ready for Stage B PR1.

---

## What Stage A Was Meant to Accomplish

Stage A ("foundation complete") had the following scope:

1. Establish canonical source authority in the `source/` tree.
2. Produce a grounded planning layer: characters, locations, props, wardrobe, and pilot
   scene cards, all connected to the screenplay source rather than scaffolded from guesses.
3. Close continuity files so the repo is not depending on ungrounded shells.
4. Produce pilot scene review/support notes that are working documents, not scaffold
   garbage.
5. Refresh stale generated reports so they reflect current repo truth.
6. Ensure the repo is defensible before Stage B PR1 begins (Omni schema additions).

Stage A explicitly excluded:
- Omni schema migration (Stage B PR1).
- visual_dev/elements and visual_dev/omni_sets (Stage B).
- Schema migration of existing YAMLs.
- Mutation of the source screenplay.
- Extension of the 120-scene contract.
- Invention of new stable IDs.
- Removal of motion_prep.

---

## Source Authority

**Complete.**

- `source/story_blueprint.md` — canonical structural source; preserved as-is.
- `source/character_dossier.md` — canonical character source; preserved as-is.
- `source/project_config.json` — canonical production configuration; preserved as-is.
- `source/style_bible.md` — style authority; preserved as-is.
- `source/continuity_bible.md` — continuity authority; preserved as-is.
- `source/location_bible.md` — location authority; preserved as-is.
- `source/screenplay/closing_price.fountain` — canonical screenplay; not mutated.
- `source/screenplay/closing_price.numbered.fountain` — generated numbered copy; intact.

All live source files pass `validate_phase1.py` with 0 errors, 0 warnings.

---

## Planning Hydration

**Complete for the Stage A priority scope.**

Hydrated records:
- Characters: `C01` through `C05` (5 records).
- Locations: `LOC001` through `LOC004` (4 records).
- Props: `PROP001`, `PROP003`, `PROP004`, `PROP005` (4 records).
- Wardrobe: `WD001` through `WD004` (4 records).
- Pilot scene cards: `SC0001`, `SC0003`, `SC0006`, `SC0008`, `SC0009` (5 records, all at
  `review` / `needs_human_review` status — awaiting human sign-off, not automation).
- Remaining 115 scene cards (`SC0002`, `SC0004–SC0007`, `SC0010–SC0120`) are scaffolded
  but not yet hydrated. This is known and expected; they are the Stage B hydration backlog.

High-confidence records: C01, C02, C04, LOC001–LOC003, PROP001/003/004, WD001/003/004,
SC0001/SC0003/SC0006.

Lower-confidence records (usable with caution, explicit uncertainty markers):
C03, C05, LOC004, PROP005, WD002, SC0008, SC0009.

The `planning_hydration_report.md` captures the full scope and remaining conflicts.

---

## Continuity Closure

**Complete for Stage A.**

- `planning/continuity/camera_grammar.yaml` — upgraded from a single scaffold placeholder
  to 8 grounded rules (CG01–CG08) covering framing, movement, lighting, object priority,
  sightline preservation, negative space, and observational register. Pre-Omni; compatible
  with Stage B migration direction.
- `planning/continuity/timeline.yaml` — upgraded from a single scaffold placeholder entry to
  grounded KNOWN/LIKELY/UNRESOLVED entries for SC0001–SC0009. SC0010–SC0120 are explicitly
  flagged as not yet grounded.
- `planning/continuity/time_of_day.yaml` — previously hydrated; not modified.
- `planning/continuity/weather.yaml` — previously hydrated; not modified.
- `planning/continuity/props_state.yaml` — previously hydrated; not modified.
- `planning/continuity/wardrobe_state.yaml` — previously hydrated; not modified.

---

## Pilot Scene Review and Support Notes

**Complete for Stage A.** All five pilot scenes (`SC0001`, `SC0003`, `SC0006`, `SC0008`,
`SC0009`) now have working notes in three files each:

### `planning/scenes/*/review_notes.md`

All five converted from scaffold template to structured working notes with:
- Current status and confidence level.
- What is confirmed (grounded from scene card / source excerpt).
- What still needs human review (specific items, not vague "review needed").
- What waits for Stage B / Omni.

### `visual_dev/motion_prep/*/motion_notes.md`

All five converted from scaffold template to pre-production notes with:
- Shot purpose grounded from scene card visual_targets.
- Start/end frame state: honestly noted as pending (no assets generated at Stage A).
- Motion description grounded from scene card movement_bias and camera grammar rules.
- Handoff tool: explicitly deferred to Stage B.

### `visual_dev/stills/*/selection_notes.md`

All five converted from scaffold template to pre-production selection guides with:
- Selection criteria checklist (unchanged structure, now contextual).
- Selection targets: priority still candidates grounded from scene content.
- Approved stills: honestly noted as none (no assets generated at Stage A).
- Rejected/notes: honest negative notes on what would contradict the scene's register.

### `visual_dev/characters/*/notes.md` and `visual_dev/locations/*/notes.md`

All five character notes (C01–C05) and four location notes (LOC001–LOC004) converted from
scaffold template to grounded pre-production notes. Where ID conflicts exist (C05, LOC004), the
notes explicitly document the hold condition and the reason.

---

## Repo Hygiene

**Complete for Stage A.**

- **Live placeholder count: 0** in all live foundation files.
- **Archival placeholder count: 266** in `evidence/provenance/` bundle files (intentionally
  ignored; these are frozen archival snapshots, not live working files).
- **Generated/refreshable placeholder count: 0** after regenerating pilot review packets
  and canon hydration queue. (Note: the `canonical_import_conflicts.md` report contains 1
  occurrence on line 74, which is within a quoted field value in a conflict description
  table, not a live scaffold.)
- Closure audit script added: `scripts/stage_a_closure_audit.py`.
  Outputs: `evidence/validation_reports/stage_a_closure_placeholder_audit.json` and `.md`.
- Pre-commit config added: `.pre-commit-config.yaml` with a no-placeholder check hook.
- Makefile extended with `closure-audit` target.

### Validation results (run on `2026-04-19`)

| Command | Result |
|---------|--------|
| `make validate` (`validate_phase1.py`) | PASS — 0 errors, 0 warnings |
| `make integrity` (`check_referential_integrity.py`) | PASS — 0 errors, 0 warnings |
| `make manifests` (`build_manifests.py`) | PASS — 120 scenes, 5 characters, 4 locations, 8 continuity records |
| `make canon-queue` | PASS — A=5, B=17, C=5, D=115, supplemental=0 |
| `make closure-audit` | PASS — 0 live blockers |

---

## Remaining External / Manual Items

The following items are outside the repo's local verification scope. **These have NOT been
verified in-repo and must not be assumed complete.**

### GitHub branch protection (live settings)

- Branch protection rules for `main` and release branches must be configured in the GitHub
  repository settings UI. The policy is documented in `docs/workflow/branch_protection_policy.md`,
  but the live GitHub settings cannot be verified from inside the repo.
- Required status checks (CI workflows that must pass before merge) must be enabled via
  the GitHub branch protection UI, not by editing files.

### DVC remote configuration

- DVC remote credentials and the live remote setup (e.g., S3, GCS, or SSH target) must be
  configured outside the repo. The repo uses DVC for large file tracking, but no remote
  has been confirmed as active in this pass.

### Zenodo live repository enablement and DOI verification

- Zenodo DOI minting and live repository enablement must be done through the Zenodo UI
  linked to the GitHub repository. The `.zenodo.json` metadata file in the repo is correct,
  but the live Zenodo repository connection and DOI issuance have not been verified in this
  pass.

### Canon-z1p1-r1 tag

- The `canon-z1p1-r1` tag has not been applied. It should be applied after a human
  reviewer confirms the Stage A closure state and signs off on the pilot scene review
  packets. The `make freeze TAG=canon-z1p1-r1` command is ready; it should not be run
  without human sign-off.

### Human review sign-off on pilot scene cards

- All five pilot scene cards are at `review_status: needs_human_review`. They are
  defensible working documents but have not received a human canon-review pass.
- The C05 compact ID drift conflict and the LOC004 / LOC001 disambiguation (SC0009) must
  be resolved by a human reviewer before any of the affected scene cards can advance to
  `approved` status.

---

## Why the Repo Is Ready for Stage B PR1

Stage A is complete in the sense that:

1. All live foundation files are free of scaffold placeholder strings.
2. The source authority layer is intact and unmodified.
3. The planning hydration layer covers the Priority A–C scope grounded from source.
4. Continuity files are real working documents, not shells.
5. Pilot review/support notes are real pre-production working notes, not scaffold garbage.
6. All local validation targets pass with 0 errors, 0 warnings.
7. No Omni migration was started. No schema migration occurred. No new stable IDs were
   invented. The 120-scene contract is unchanged. The source screenplay was not mutated.
   Evidence/provenance archival bundles were not treated as live blockers.

Stage B PR1 may now begin adding Omni schema fields and visual_dev/elements structure
on top of this foundation without encountering unresolved scaffold debt in the areas
covered by Stage A.
