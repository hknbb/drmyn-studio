# DRMYN Studio — Metadata-Only Human-Agent Film Production Workflow

This repository contains the canonical planning, prompt-governance, validation, and reproducibility infrastructure for **DRMYN Studio**, demonstrated through **Zone 1 / Phase 1** of the *Closing Price* AI-assisted film project.

## Purpose

DRMYN Studio is the **pre-production and prompt-engineering layer** of the AI-assisted film production pipeline. It is responsible for:

- defining canonical source truth
- stabilizing scene, character, location, continuity, and prompt records
- enforcing naming and schema rules
- supporting GitHub-based review and approval
- generating reproducible artifacts before downstream runtime generation

This repository is **not** the runtime output layer. Runtime graph artifacts, event logs, and materialized indices belong to later stages of the broader Nexus Zero pipeline.

## Core principles

1. **Source-first** — Canonical project truth begins in `source/`.
2. **Stable identifiers** — Scene, character, sequence, location, prop, and continuity IDs must remain stable across the pipeline.
3. **Schema-first planning** — Planning records are only accepted if they pass machine validation.
4. **Prompt governance** — Prompts move through a strict lifecycle: `draft → review → approved → locked`.
5. **GitHub review before canon** — Nothing becomes canonical without review, validation, and merge to the protected base branch.
6. **Reproducibility by design** — Validation reports, manifests, artifact bundles, and release metadata are treated as first-class research outputs.

## Repository layout

| Directory | Purpose |
|-----------|---------|
| `source/` | Canonical human-authored source files |
| `planning/` | Scene cards, character sheets, location sheets, continuity records |
| `prompts/` | Prompt lifecycle and library |
| `schemas/` | JSON Schemas for machine validation |
| `scripts/` | Validation and artifact scripts |
| `evidence/` | Maps, logs, and reports for publication and supplements |
| `.github/` | GitHub-native governance and CI files |
| `docs/` | Human-readable workflow, methodology, and policy documentation |

## Zone 1 / Phase 1 scope

**In scope:**
- Canonical source package preparation
- Scene-card construction
- Prompt-brief design
- Continuity registration
- GitHub review and approval workflows
- Artifact validation and release

**Out of scope:**
- Runtime graph generation
- Scene drafting
- LLM critique
- Commit-event writing
- Index materialization

## Validation

Run locally:

```bash
pip install -r requirements.txt

python scripts/validate_phase1.py \
  --source-dir source \
  --planning-dir planning \
  --prompts-dir prompts \
  --schemas-dir schemas \
  --evidence-dir evidence \
  --report-json evidence/validation_reports/phase1_validation_report.json \
  --report-md evidence/validation_reports/phase1_validation_report.md

python scripts/check_referential_integrity.py \
  --planning-dir planning \
  --prompts-dir prompts \
  --output evidence/validation_reports/referential_integrity_report.json

python scripts/build_manifests.py \
  --planning-dir planning \
  --output-dir planning/manifests
```

Or use Make:

```bash
make validate
make manifests
make numbered-fountain
make seed-scenes
make hydrate-scenes
make canon-queue
```

## Source spine automation

- `source/screenplay/closing_price.fountain` remains the canonical unnumbered screenplay.
- `planning/manifests/closing_price_scene_retrieval_map.json` is the authoritative 120-scene spine.
- `make numbered-fountain` generates `source/screenplay/closing_price.numbered.fountain` as a derivative artifact.
- `make seed-scenes` scaffolds `planning/scenes/SC0001` through `planning/scenes/SC0120` and refreshes `scene_excerpt.md` from the retrieval-map spans.
- `make hydrate-scenes` conservatively grounds `scene_card.yaml` and `prompt_brief.md` from the retrieval map and each scene's excerpt, then writes `evidence/validation_reports/scene_hydration_report.json`.
- `make canon-queue` builds a deterministic canon hydration work queue plus pilot-scene review packets for the first human canon pass.

## Branching model

- `main` — protected, release-ready only
- Feature branches — short-lived working branches
- No direct commits to `main`

See [docs/workflow/branch_protection_policy.md](docs/workflow/branch_protection_policy.md).

## ID namespace

| Entity | Format | Example |
|--------|--------|---------|
| Scene | `SC0001` | `SC0001` |
| Character | `C01` | `C01` |
| Sequence | `SEQ01` | `SEQ01` |
| Location | `LOC001` | `LOC001` |
| Prop | `PROP001` | `PROP001` |
| Wardrobe | `WD001` | `WD001` |

## Scientific Clean Release / Reviewer Entrypoint

The Human-Agent Production Copilot layer (HA-0 → HA-6) is complete and merged.
For journal reviewers and reproducibility auditors, the canonical entrypoint is:

```
docs/publication/scientific_clean_release_manifest.md
```

That document describes what is included, what is excluded, validation commands,
the storage doctrine, AI model provenance, and known limitations.

Quick validation:

```bash
python -m pytest -q
python scripts/validate_production_records.py --repo-root .
python scripts/validate_prompt_records.py --repo-root .
```

## Citation

If you use this repository in a publication, please cite it using the metadata in [CITATION.cff](CITATION.cff).

## Archiving

Tagged releases are archived via Zenodo. Metadata is stored in [.zenodo.json](.zenodo.json).

## License

See [LICENSE](LICENSE).
