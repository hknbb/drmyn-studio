# Local Manual Storage Playbook

HA-2 defines how the human operator stores production media outside the git repo
while keeping repository records auditable. This playbook is manual by design:
the repo does not call Google Drive APIs, cloud SDKs, or credential-backed sync
tools.

## Root Folders

Use one stable storage root name across local disk and Google Drive:

```text
ClosingPriceMedia/
```

Recommended local examples:

```text
D:/ClosingPriceMedia/
E:/ClosingPriceMedia/
```

Recommended Google Drive example:

```text
My Drive/ClosingPriceMedia/
```

Repository metadata should refer to those locations with URI-style references,
not absolute machine paths:

```yaml
external_storage_ref: "local://ClosingPriceMedia/video/SC0006/take001.mp4"
external_storage_ref: "gdrive://ClosingPriceMedia/video/SC0006/take001.mp4"
```

## Folder Layout

```text
ClosingPriceMedia/
  elements/
    characters/
      C01/
        candidates/
        rejected/
        canonical_backups/
    locations/
      LOC001/
        candidates/
        rejected/
    props/
      PROP001/
        candidates/
        rejected/
    wardrobe/
      WD001/
        candidates/
        rejected/
  storyboards/
    SC0006/
      candidates/
      locked_keyframes/
  video/
    SC0006/
      takes/
      selected/
  post/
    proxies/
      SC0006/
    audio/
    exports/
```

## Naming

Use lowercase descriptive names with stable numeric suffixes:

```text
nadia_front_001.png
nadia_front_002.png
hospital_corridor_wide_001.png
SC0006_take001.mp4
SC0006_take001_proxy.mp4
```

For scene video, keep the scene id and take number at the front:

```text
video/SC0006/takes/SC0006_take001.mp4
video/SC0006/selected/SC0006_take003_selected.mp4
```

## What Goes Where

| Media | Preferred reference | Notes |
|---|---|---|
| Extra element candidates beyond repo/LFS limit | `local://` or `gdrive://` | Repo keeps metadata path only. |
| Rejected bulk image outputs | `local://` or `gdrive://` | Do not commit. |
| Storyboard candidate stills | `local://` or `gdrive://` | Do not commit candidate folders. |
| Full Kling video takes | `local://`, `gdrive://`, or future `dvc://` | Never commit video binaries. |
| Post-production proxies | `local://`, `gdrive://`, or future `dvc://` | Repo stores references only. |
| Platform job ids | `kling://...` | This is not a storage location. |

## Manual Sync Procedure

1. Save generated media under `ClosingPriceMedia/` using the folder layout above.
2. If using Google Drive, manually upload or sync the same relative path.
3. Record the chosen URI in metadata, for example:

   ```yaml
   external_storage_ref: "gdrive://ClosingPriceMedia/video/SC0006/takes/SC0006_take001.mp4"
   repo_binary_committed: false
   storage_status: pending_external
   ```

4. After the human verifies the file exists in the referenced storage location,
   update only metadata fields allowed by the relevant schema and PR workflow.
5. Never paste Drive tokens, sharing secrets, local credential paths, or signed
   URLs into repo files.

## Verification Checklist

- The referenced file exists outside the git repo.
- The repo contains only YAML, CSV, Markdown, prompt text, schemas, or allowed
  Git LFS assets.
- `repo_binary_committed` is `false` for video, proxy, audio render, and bulk
  candidate outputs.
- URI prefixes use `local://`, `gdrive://`, `dvc://`, `s3://`, or `kling://`.
- No absolute local path such as `C:/Users/...` or `D:/...` appears in committed
  production metadata.

## Current Boundary

HA-2 is docs-only. It does not add storage automation, Google Drive API calls,
new schemas, local media index records, dashboard UI, PR helpers, or lifecycle
promotion.
