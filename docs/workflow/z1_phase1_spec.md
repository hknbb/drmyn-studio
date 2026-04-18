# Zone 1 / Phase 1 Specification

## Purpose

Zone 1 / Phase 1 is the canonical pre-production and prompt-engineering layer of the Closing Price / Nexus Zero workflow. It defines source truth, stabilizes planning records, governs the prompt lifecycle, and produces reproducible artifacts before runtime generation begins.

## Scope

**In scope:**
- Canonical source package (`source/`)
- Scene card construction (`planning/scenes/`)
- Character and location sheets (`planning/characters/`, `planning/locations/`)
- Prop and wardrobe records (`planning/props/`, `planning/wardrobe/`)
- Continuity registration (`planning/continuity/`)
- Prompt brief design (`planning/scenes/SCxxxx/prompt_brief.md`)
- Prompt lifecycle governance (`prompts/`)
- GitHub review and approval
- Validation, manifests, artifact release

**Out of scope:**
- Runtime graph generation
- LLM scene drafting
- Critique, commit-event writing
- Index materialization
- Generated still/clip assets

## Key contracts

1. Every scene card must pass `scene_card.schema.json` validation before merge.
2. Every character referenced in a scene card must have a corresponding `planning/characters/Cxx.yaml`.
3. Every location referenced in a scene card must have a corresponding `planning/locations/LOCxxx.yaml`.
4. Prompts may only enter production from the `approved/` folder.
5. Canon-locked records may not be modified without a canon change request.

## Definition of Done

Phase 1 is complete when:

- [ ] All source files in `source/` are filled and approved
- [ ] All scenes have a schema-validated `scene_card.yaml`
- [ ] All characters and locations have planning records
- [ ] Continuity records are separated by type
- [ ] At least the first prompt package is in `approved/`
- [ ] CI validation passes on `main`
- [ ] `CITATION.cff`, `LICENSE`, `.zenodo.json`, `devcontainer.json`, `dependabot.yml` are in repo root
- [ ] A `canon-z1p1-r1` release has been created
- [ ] Artifact bundle is downloadable
- [ ] Article 3 target scenes are flagged in `evidence/scene_prompt_map.csv`
