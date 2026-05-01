# Production Output Storage Policy

**Batch 0.75 — Applies to all subsequent batches.**

This document defines where every category of production output lives.
No agent, script, or manual step may deviate from these rules without a PR that updates this file first.

---

## Governing Principle

The repo tracks **decisions, metadata, and small canonical assets**.
The repo does **not** host generated video, bulk render output, or unlimited-size image collections.

> If a file can be regenerated from a prompt record + model, it belongs in external storage.
> If a file is a locked canonical identity anchor (≤ 20 images per element), it belongs in repo + LFS.

---

## Storage Decision Table

| Asset type | Location | Git LFS? | Max per pack | Notes |
|---|---|---|---|---|
| Canonical element images (`visual_dev/elements/{type}/{id}/`) | Repo + Git LFS | ✅ already configured | N/A | `.gitattributes` covers `visual_dev/elements/**/*.{png,jpg,jpeg,webp}` |
| Candidate images (`visual_dev/elements/{type}/{id}/candidates/`) | Repo + Git LFS | ✅ (same LFS rule) | ≤ 20 per element | Beyond 20 → external storage; repo stores path ref only |
| Rejected bulk outputs from external generation | External storage only | ❌ | 0 | Never committed; only selected candidates enter repo |
| Locked storyboard keyframes (`visual_dev/storyboards/SC####/`) | Repo + Git LFS | ✅ added Batch 0.75 | ≤ 5 per scene | Only the single human-selected keyframe per option; candidate stills stay external |
| Storyboard candidate stills (unselected) | External storage | ❌ | 0 | Volume too high for LFS; repo stores `external_storage_ref` in `storyboard_options.yaml` |
| Kling video takes (full MP4 / MOV) | External DVC-style storage | ❌ | 0 | Repo stores `platform_asset_ref` + `external_storage_ref` in `video_takes.yaml`; `repo_binary_committed: false` required |
| Post-production proxies (`post/edit/proxies/`) | External storage | ❌ | 0 | Repo stores path reference only |
| Post-production audio renders (`post/sound/mixes/`, `post/dialogue/`) | External storage | ❌ | 0 | Exception: small LUT files (< 1 MB) may be committed directly to `post/color/luts/` |
| LUT files (`post/color/luts/`) | Repo (no LFS) | ❌ | N/A | Typically < 1 MB; committed as regular binary if ≤ 1 MB |
| YAML metadata (all `evidence/`, `visual_dev/**/*.yaml`) | Repo (text) | ❌ | N/A | Always plain git; never LFS |
| Prompt records (`prompts/`) | Repo (text) | ❌ | N/A | Always plain git |
| Schema files (`schemas/`) | Repo (text) | ❌ | N/A | Always plain git |

---

## Git LFS Scope

### Currently active (Stage B PR4B)

```gitattributes
visual_dev/elements/**/*.png  filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.jpg  filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
visual_dev/elements/**/*.webp filter=lfs diff=lfs merge=lfs -text
```

### Added in Batch 0.75 (locked storyboard keyframes)

```gitattributes
visual_dev/storyboards/**/*.png  filter=lfs diff=lfs merge=lfs -text
visual_dev/storyboards/**/*.jpg  filter=lfs diff=lfs merge=lfs -text
visual_dev/storyboards/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
visual_dev/storyboards/**/*.webp filter=lfs diff=lfs merge=lfs -text
```

**Scope discipline:** LFS rules are always path-scoped.
`visual_dev/elements/**` and `visual_dev/storyboards/**` are separate scopes.
Global `*.png` or similar patterns are **never** added.

---

## .gitignore Protections Added in Batch 0.75

The following patterns prevent accidental binary commits:

```gitignore
# Kling / video take binaries — external storage only
visual_dev/omni_sets/**/takes/*.mp4
visual_dev/omni_sets/**/takes/*.mov

# Post-production proxy binaries — external storage only
post/edit/proxies/**/*.mp4
post/edit/proxies/**/*.mov
post/edit/proxies/**/*.mkv
post/edit/proxies/**/*.wav

# Storyboard candidate stills — external storage only; repo holds metadata
visual_dev/storyboards/**/candidates/
```

---

## External Storage Convention (Phase 1)

DVC remote is not yet configured in this repo.
Until it is, external storage references use the following convention in YAML metadata fields:

```yaml
external_storage_ref: "dvc://closing-price/{scene_id}/{filename}"
platform_asset_ref:   "kling://{platform-job-id}"
repo_binary_committed: false
```

These are **placeholder conventions** that will resolve to real storage paths once a DVC remote is configured.

**Do not treat `external_storage_ref` as a verified storage location in Phase 1.**
Flag any record with `external_storage_ref` set but unverified as `storage_status: pending_external`.

---

## URI Prefix Vocabulary (HA-2)

HA-2 adds an explicit vocabulary for manual local and Google Drive storage
references. This is a convention only: no Google Drive API, cloud SDK, sync
daemon, or credential flow is introduced by this repo.

| Prefix | Meaning | Example | Current status |
|---|---|---|---|
| `local://ClosingPriceMedia/...` | File is stored on the operator's local disk outside the git repo. | `local://ClosingPriceMedia/elements/characters/C01/candidates/nadia_001.png` | Manual, operator-verified |
| `gdrive://ClosingPriceMedia/...` | File is stored in the operator's Google Drive folder by manual upload/sync. | `gdrive://ClosingPriceMedia/video/SC0006/take001.mp4` | Manual, no API |
| `dvc://...` | Future DVC-addressable storage reference. | `dvc://closing-price/SC0006/take001.mp4` | Optional future convention |
| `s3://...` | Future S3/object-storage reference. | `s3://closing-price/video/SC0006/take001.mp4` | Optional future convention |
| `kling://platform_id` | Kling platform asset or job identifier. | `kling://job_12345` | Platform reference only |

Existing `external_storage_ref` strings are not backfilled in HA-2. Future
schemas may add a `storage_backend` enum for new record types such as handoff
or local media index records, but this PR does not rewrite existing production
metadata.

For manual folder structure and naming conventions, see
`docs/operator_guides/local_manual_storage_playbook.md`.

---

## Candidate Image Limit

To prevent LFS bloat, candidate image counts are capped:

| Category | Repo + LFS limit | Action beyond limit |
|---|---|---|
| Character element candidates | ≤ 20 per element | Additional candidates → external storage; repo stores path ref |
| Location element candidates | ≤ 20 per element | Same |
| Prop element candidates | ≤ 20 per element | Same |
| Style reference candidates | ≤ 20 per category | Same |

When the limit is reached, the Image Review Agent must record the external path in `image_selection.yaml` rather than committing the file.

---

## Storyboard Keyframe Policy

Only **selected, locked keyframes** are committed to `visual_dev/storyboards/SC####/frames/`.

| Storyboard file type | Repo status |
|---|---|
| `storyboard_options.yaml` (metadata) | Repo (text, plain git) |
| Candidate stills generated externally | External storage only; path ref in YAML |
| Selected locked keyframe (1 per option, human-approved) | Repo + Git LFS |

Storyboard candidate stills must never be committed. The `visual_dev/storyboards/**/candidates/` pattern in `.gitignore` enforces this.

---

## Video Take Policy

All Kling Omni video take files (`.mp4`, `.mov`) are **external storage only**.

The `video_takes.yaml` record format must include:

```yaml
takes:
  - take_id: SC0001_TAKE001
    platform_asset_ref: "kling://{platform-job-id}"
    external_storage_ref: "dvc://closing-price/SC0001/take001.mp4"
    local_proxy_ref: null
    repo_binary_committed: false
    status: rejected | selected | candidate
```

Any record with `repo_binary_committed: true` must be flagged as a `storage_policy_violation`.

---

## Summary: "When in doubt" Rule

> **Text / YAML / metadata → repo (plain git).**
> **Small canonical images (≤ 20/element) → repo + LFS.**
> **Everything else (video, render, proxy, bulk stills) → external storage, repo holds reference only.**

---

*Introduced: Batch 0.75. Maintained by: human PR only.*
