# Release Notes - v0.4.6

**Release state:** v0.4.6 - Scientific clean sync release  
**Release date:** 2026-05-11  
**Zenodo DOI:** https://doi.org/10.5281/zenodo.20121045

## Summary

v0.4.6 publishes the latest scientific-clean repository state with rollout stabilization fixes and post-release citation metadata synchronization.

## Included

- Rollout stabilization polish (Kling prompt sanitization, Critic per-shot segment hardening, Midjourney metadata/comment normalization)
- SC0001 prompt lifecycle clean-start alignment
- Public release synchronization for scientific archiving

## Citation Metadata Sync

The following files were synchronized to v0.4.6 and DOI `10.5281/zenodo.20121045`:

- `CITATION.cff`
- `.zenodo.json`
- `codemeta.json`
- `README.md` citation block
- `docs/publication/software_citation.md`
- `docs/publication/article_metadata.md`
- `docs/publication/scientific_clean_release_manifest.md`

## Validation Snapshot

- `python -m pytest -q` -> `1247 passed`
