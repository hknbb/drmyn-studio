# visual_dev/elements — Canonical Element Packs

Folder scaffolding introduced in **Stage B PR2**.
Metadata-only pilot packs added in **Stage B PR4C** for the five pilot scenes
(characters C01–C03, C05; locations LOC001, LOC002, LOC004; props PROP001, PROP003).
Each pack contains a `pack_manifest.yaml` and `source_notes.md`; no reference images
are committed yet — image seeding remains blocked pending source assets.

## Sub-folders

| Folder | Contents |
|---|---|
| `characters/` | Per-character canonical element packs (reference images, LoRA anchors) |
| `locations/` | Per-location canonical element packs (establishing frames, lighting refs) |
| `props/` | Per-prop canonical element packs (isolated reference images) |
| `style_refs/` | Cross-scene style references (colour boards, LUT previews, tone samples) |

## Storage doctrine

| Asset type | Where it lives |
|---|---|
| Canonical reference packs (small images, YAML descriptors) | This repo / Git LFS |
| Generated video clips, rendered outputs | External DVC-style storage (not yet configured) |
| Kling / Runway / Pika source binaries | Platform storage; paths logged in `omni_generation_record` files |

**Do not commit large binaries directly to this folder.**
Git LFS is configured (Stage B PR4B) for canonical image assets under this
tree: `*.png`, `*.jpg`, `*.jpeg`, and `*.webp` files anywhere inside
`visual_dev/elements/` are LFS-tracked. YAML descriptor files and other
text metadata remain regular git files and are not LFS-tracked.
Generated video/render outputs and platform-origin binaries belong in
external storage, not here; no DVC remote is configured yet.
