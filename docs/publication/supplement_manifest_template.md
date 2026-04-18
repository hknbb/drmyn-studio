# Supplement Manifest Template

Use this template when preparing the article supplement package.

---

## Supplement: Closing Price — Zone 1 / Phase 1 Artifact Package

**Release tag:** `<release-tag>`
**Zenodo DOI:** `<zenodo-doi>`
**Date:** `<YYYY-MM-DD>`

---

## Included files

| File | Description |
|------|-------------|
| `scene_index.csv` | Index of all Phase 1 scenes (filtered to article-3 set) |
| `character_index.csv` | Character planning index |
| `location_index.csv` | Location planning index |
| `scenes/SC0001/scene_card.yaml` | Scene card for SC0001 |
| `prompts_approved/SC0001__*.yaml` | Approved prompt records for SC0001 |
| `validation_reports/phase1_validation_report.json` | CI validation report |
| `canon_manifest.json` | Canon freeze manifest with SHA-256 hashes |

---

## How to verify

```bash
sha256sum -c bundle_sha256.txt
```

---

## Citation

See `CITATION.cff` in the repository root.
