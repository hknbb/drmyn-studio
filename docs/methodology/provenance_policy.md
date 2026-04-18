# Provenance Policy

## Principles

1. Every canonical record must be traceable to a specific PR and commit.
2. Every approval must be logged in `evidence/approval_log.csv`.
3. Every canon freeze must produce a SHA-256 manifest.
4. Validation reports must be stored as GitHub Actions artifacts.

## Source authority

- `source/story_blueprint.md` is the canonical structural source.
- `source/character_dossier.md` is the canonical character authority source.
- `source/project_config.json` is the canonical production configuration source.
- Generated scene cards, manifests, and downstream planning artifacts must adapt to these source files rather than overwrite them.

## Record provenance fields

All planning records support optional `provenance` fields:
- `created_by` — GitHub username or identifier
- `created_at` — ISO 8601 datetime
- `updated_by`
- `updated_at`
- `git_commit` — short or full commit hash

## Approval log

`evidence/approval_log.csv` tracks all status changes for scenes, characters, locations, and prompts.

Columns: `record_type, record_id, action, approved_by, approved_at, note`

## Canon freeze provenance

Each freeze creates:
- `evidence/provenance/<tag>/canon_manifest.json` — file list with SHA-256 hashes
- `evidence/provenance/<tag>/canon_freeze_summary.md` — human-readable summary
- `evidence/provenance/<tag>/bundle_sha256.txt` — ZIP bundle hash
