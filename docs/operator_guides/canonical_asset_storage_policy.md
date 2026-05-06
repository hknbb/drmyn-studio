# Canonical Asset Storage Policy

This document defines the two storage categories for production assets in this
repo and the rules for transitioning between them. Read this before B8A or any
canonical asset intake PR.

## Two Asset Categories

### Category 1: Canonical Reference Assets

Canonical reference assets are approved, human-sourced reference images for
characters, locations, props, and wardrobe. They are:

- acquired by the human operator (photographed, licensed, or publicly sourced);
- reviewed for copyright and provenance before any commit;
- committed to the repo via **Git LFS** under `visual_dev/elements/**/*.png/jpg/jpeg/webp`;
- the authoritative visual ground truth for T2I prompt generation and scene production.

`storage_policy` value after human review and PR approval:

```text
git_lfs_approved_references_only
```

### Category 2: Generated Production Outputs

Generated outputs are T2I image batches, video takes, proxy renders, and other
model-generated assets. They are:

- produced externally (T2I platform, Kling, post-production tools);
- large in volume and not auditable as canonical references;
- stored **outside the repo** in the operator's designated external storage;
- never committed to the repo, even via LFS.

`storage_policy` value (permanent, never changes):

```text
no_binary_commits
```

## Git LFS Rules

`.gitattributes` already defines LFS routing for canonical reference image types:

```text
visual_dev/elements/**/*.png  filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.jpg  filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.webp filter=lfs diff=lfs merge=lfs -text
```

Generated storyboard candidates and video takes are **gitignored**, not LFS-tracked:

```text
visual_dev/storyboards/**/candidates/     # gitignored
visual_dev/omni_sets/**/takes/*.mp4       # gitignored
visual_dev/intake_staging/                # gitignored (auto-placement staging)
```

## Intake Slot Lifecycle

Each `intake_slot.yaml` file tracks one element group's canonical reference set.

### Initial state (set by B7C/B7D scaffolding)

```yaml
source_status: not_collected
copyright_review: pending
provenance_review: pending
intake_ready_to_proceed: false
canonical_assets_committed: []
storage_policy: no_binary_commits
```

### After B8A human intake PR (first real canonical assets)

The human operator, in a reviewed PR, may update:

```yaml
source_status: source_images_in_repo        # all required_views committed via LFS
copyright_review: approved                  # human confirmed rights
provenance_review: approved                 # human confirmed source chain
canonical_assets_committed:                 # repo-relative LFS paths
  - visual_dev/elements/characters/C01/wardrobe/WD001/c01_wd001_front.jpg
  - visual_dev/elements/characters/C01/wardrobe/WD001/c01_wd001_three_quarter.jpg
  - visual_dev/elements/characters/C01/wardrobe/WD001/c01_wd001_context.jpg
storage_policy: git_lfs_approved_references_only
```

`intake_ready_to_proceed` remains **false** until a separate human decision in a
later PR. It is not set by the intake placement script or by any agent.

## Who May Change storage_policy

Only the human operator may change `storage_policy` from `no_binary_commits` to
`git_lfs_approved_references_only`. This change must:

1. Appear in a PR dedicated to that element group's intake.
2. Include the actual committed LFS asset paths in `canonical_assets_committed`.
3. Include confirmed `copyright_review: approved` and `provenance_review: approved`.
4. Pass `validate_production_records.py` (intake_slot schema validation).

Agents must never change `storage_policy`, `intake_ready_to_proceed`, copyright
completion, or provenance completion fields. These remain human-gated lifecycle
fields under the same invariant as `pack_status` and `canon_lock`.

## B8A Scope Guard

B8A is the first real canonical asset intake. It is limited to:

```text
visual_dev/elements/characters/C01/wardrobe/WD001/
```

B8A must not:

- change any other intake_slot.yaml's storage_policy;
- lock packs;
- run Kling generation;
- promote lifecycle state in any other element;
- include generated T2I images as canonical reference assets;
- add assets outside the one approved slot.

## Forbidden for All Agents

Agents must not:

- commit image, video, audio, or proxy binaries in any element directory;
- change `storage_policy` in any `intake_slot.yaml`;
- set `intake_ready_to_proceed: true`;
- set `copyright_review: approved` or `provenance_review: approved`;
- claim pack completion or lifecycle promotion.

See also: [agent_role_contract.md](agent_role_contract.md)
