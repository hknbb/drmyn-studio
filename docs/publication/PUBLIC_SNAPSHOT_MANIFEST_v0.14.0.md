# Public Snapshot Manifest v0.14.0

## Include (public scientific snapshot)
- `schemas/`
- `scripts/`
- `tests/`
- `planning/`
- `visual_dev/` metadata YAML records
- `evidence/operator_guides/`
- `evidence/reports/`
- `model_guidance_snapshots/`
- `README.md`
- `LICENSE`
- `CITATION.cff`
- `CHANGELOG.md`
- `docs/publication/RELEASE_NOTES_v0.14.0.md`
- `docs/publication/repository_hygiene_audit_v0.14.0.md`

## Exclude (must remain out of public snapshot)
- raw generated images
- raw Kling videos
- platform downloads/export bundles
- local machine paths and local-only config artifacts
- API keys/secrets/tokens
- private media archives and large preview batches
- any binary production outputs

## Rationale
This snapshot is a metadata-only governance checkpoint and must remain reproducible, schema-valid, and free of media binaries and secrets.
