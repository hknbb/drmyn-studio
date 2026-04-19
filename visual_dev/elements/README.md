# visual_dev/elements — Canonical Element Packs

Introduced in **Stage B PR2** as folder scaffolding only.
No element packs are stored here yet; population is a PR3 task.

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
| Kling / Runway / Pika source binaries | Platform storage; paths logged in `omni_generation_record` JSON |

**Do not commit large binaries directly to this folder.**
LFS tracking rules are defined in `.gitattributes`.
External storage integration will be wired in a later phase.
