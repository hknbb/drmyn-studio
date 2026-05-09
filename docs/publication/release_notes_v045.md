# Release Notes — v0.4.5

**Release state:** v0.4.5 — Scientific clean metadata alignment release  
**Date:** 2026-05-09  
**Tests:** 548 passed  

## Summary

v0.4.5 is a metadata-only release. No source code, schemas, planning records, or pipeline logic was changed. It exists to produce a clean Zenodo archive snapshot that includes the S-PUB-1 public metadata alignment (PR #20), which was merged to main after the v0.4.4 tag was created.

## Why v0.4.5?

The v0.4.4 GitHub release and Zenodo archive (DOI: 10.5281/zenodo.20059941) were created on 2026-05-06, before the S-PUB-1 metadata consistency patch (merged 2026-05-09). The v0.4.4 Zenodo snapshot therefore contains stale citation metadata. Rather than force-moving the v0.4.4 tag (which is unsafe in academic archives), v0.4.5 is issued as the aligned release.

## Changes from v0.4.4

All changes are in publication/citation metadata files only:

| File | Change |
|---|---|
| CITATION.cff | version 0.4.4 → 0.4.5; doi uses concept DOI pending version DOI assignment |
| .zenodo.json | version 0.4.4 → 0.4.5 |
| codemeta.json | version 0.4.4 → 0.4.5; identifier uses concept DOI |
| README.md | Citation section: version 0.4.4 → 0.4.5 |
| docs/publication/scientific_clean_release_manifest.md | Release state → v0.4.5; test count 548 |
| docs/publication/software_citation.md | version 0.4.4 → 0.4.5; version DOI pending |
| docs/publication/article_metadata.md | version 0.4.4 → 0.4.5; archived DOI pending |

## Zenodo DOI

Concept DOI (always latest): https://doi.org/10.5281/zenodo.19987410  
Version DOI (v0.4.5): **pending** — to be recorded via S-PUB-2b after Zenodo archives this release.

## Test verification

```
python -m pytest -q  →  548 passed
```

## Next step

After Zenodo assigns the v0.4.5 version DOI, perform S-PUB-2b: update the version DOI in CITATION.cff, software_citation.md, article_metadata.md, and any other machine-readable metadata files.
