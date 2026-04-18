# Artifact Policy

## Phase 1 artifacts

| Artifact | Location | Retention |
|----------|----------|-----------|
| Validation report (JSON) | `evidence/validation_reports/` | Per release |
| Validation report (MD) | `evidence/validation_reports/` | Per release |
| Integrity report (JSON) | `evidence/validation_reports/` | Per release |
| Manifests (CSV) | `planning/manifests/` | Committed to repo |
| Canon manifest (JSON) | `evidence/provenance/<tag>/` | Per freeze |
| Canon freeze summary (MD) | `evidence/provenance/<tag>/` | Per freeze |
| Artifact bundle (ZIP) | GitHub Release assets | Permanent |
| SBOM (JSON) | `evidence/provenance/` | Per workflow run |

## GitHub Actions artifact retention

Validation artifacts: 14 days.
Freeze bundles: 30 days.
Release assets: permanent (attached to GitHub Release).

## Publication supplement artifacts

For article 3 supplements, use `scripts/export_artifact_bundle.py` to produce a publication-ready ZIP. Include:
- Scene cards for all article-3 flagged scenes
- Approved prompt records for those scenes
- Validation reports
- Manifests

Flag article-3 scenes in `evidence/scene_prompt_map.csv` using the `article3_flag` column.
