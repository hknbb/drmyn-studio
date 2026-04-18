# Article 3 — Method Notes

## Workflow chain

The method section of article 3 should describe the following chain:

```
screenplay excerpt → scene selection → scene card (SC0001)
  → prompt brief → prompt record (draft → approved)
  → still generation → clip generation
  → qualitative coding
```

## Evidence chain requirements

For each production scene in article 3:

1. Scene ID must appear in `evidence/scene_prompt_map.csv` with `article3_flag = true`
2. A schema-validated `scene_card.yaml` must exist
3. At least one `approved` prompt record must exist for the scene
4. The prompt→asset mapping must be traceable in `evidence/prompt_asset_map.csv`
5. Validation reports must be available as GitHub Actions artifacts or in the release bundle

## Reproducibility claim

The method section can claim reproducibility at the planning and validation level (Phase 1). Generation outputs are not deterministically reproducible due to model non-determinism.

## Artifact supplement

The article supplement should include:
- `scene_index.csv` — filtered to article-3 scenes
- `scene_card.yaml` files for those scenes
- Approved prompt records for those scenes
- `phase1_validation_report.json`
- `canon_manifest.json` from the relevant freeze tag
- DOI (Zenodo) for the release

## Notes

Document the exact freeze tag, GitHub Actions run URL, and Zenodo DOI used for
the article submission so the supplement can point to one stable evidence chain.
