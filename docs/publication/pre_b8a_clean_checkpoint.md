# Pre-B8A Clean Checkpoint

This note defines the intended clean checkpoint immediately before B8A, the
first real canonical image asset intake for
`visual_dev/elements/characters/C01/wardrobe/WD001/`.

## Purpose

This checkpoint is the last asset-free, reproducible production state before
canonical reference images enter the repository.

It is meant to support two things:

1. a clean human-reviewed starting point for B8A
2. a rollback point if later intake work needs to be unwound

## Scope Guard

At this checkpoint, the repository still contains:

- no real canonical image assets
- no generated image, video, or audio production outputs
- no pack locks
- no lifecycle promotion
- no Kling generation

The pre-B8A clean reset audit is metadata-only and does not delete, move, or
copy files.

## Intended Release Marker

Recommended private/public tag and release name:

`v0.4.1-pre-b8a-clean`

Suggested release title:

`DRMyn Studio v0.4.1: Pre-B8A Clean Production Checkpoint`

## Rollback

Recommended recovery command:

```bash
git switch -c recovery/pre-b8a-clean v0.4.1-pre-b8a-clean
```

## Related Records

- `evidence/pre_b8a_clean_resets/SC0001_pre_b8a_clean_reset.yaml`
- `docs/publication/scientific_clean_release_manifest.md`
- `docs/operator_guides/canonical_asset_storage_policy.md`
