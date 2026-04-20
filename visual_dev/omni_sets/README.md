# visual_dev/omni_sets — Per-Scene Omni Generation Sets

Introduced in **Stage B PR2** as folder scaffolding only.
No generation records or element selections are stored here yet.

- **PR3** — scene card Omni field hydration: populate `omni_set_ref` and related fields in each scene card across all 120 scenes
- **PR4** — actual element selections and generation records for pilot scenes placed here

## Structure

```
visual_dev/omni_sets/
  SC0001/
    elements_used/   ← symlinks or refs to elements selected for this scene
    generations/     ← omni_generation_record files for this scene
  SC0002/
    ...
  SC0120/
    ...
```

Each scene folder maps 1:1 to a scene card in `planning/scenes/`.
The `omni_set_ref` field added to the scene card schema in Stage B PR1
will point to the records stored here once PR3 hydration runs.

## Storage doctrine

| Asset type | Where it lives |
|---|---|
| `omni_generation_record` files (metadata only) | This repo |
| Generated video/image binaries | External DVC-style storage (not yet configured) |
| Selected element refs (small descriptors) | This repo or Git LFS |

**Do not commit large generated binaries here.**
Output file paths are tracked inside `omni_generation_record` files;
the binaries themselves will move to external storage in a later phase.
