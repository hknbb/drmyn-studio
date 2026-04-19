# deliverables — Final Output Tree

Introduced in **Stage B PR2** as folder scaffolding only.
All sub-folders are empty (`.gitkeep` only) until output packaging begins.

## Sub-folders

| Folder | Contents |
|---|---|
| `masters/` | Finished master exports (full-res, archival format) |
| `submissions/` | Platform-specific delivery packages (aspect ratio, codec variants) |
| `archives/` | Compressed project archives and source bundles |

## Storage doctrine

| Asset type | Where it lives |
|---|---|
| Delivery manifests and checksums (small text) | This repo |
| Master video files | External DVC-style storage (not yet configured) |
| Submission packages | External storage; references logged in delivery records |

**Do not commit large video files here.**
Final deliverable binaries will be managed via external storage
in a later phase. Checksums and delivery manifests will remain in-repo
for audit trail purposes.
