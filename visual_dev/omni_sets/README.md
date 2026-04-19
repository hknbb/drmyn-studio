# visual_dev/omni_sets — Per-Scene Omni Generation Sets

Introduced in **Stage B PR2** as folder scaffolding only.
No generation records or element selections are stored here yet;
population is a PR3 task (scene card Omni field hydration).

## Structure

```
visual_dev/omni_sets/
  SC0001/
    elements_used/   ← symlinks or refs to elements selected for this scene
    generations/     ← omni_generation_record JSON files for this scene
  SC0002/
    ...
  SC0120/
    ...
```

Each scene folder maps 1:1 to a scene card in `planning/scenes/`.
The `element_set_id` and `omni_set_ref` fields in the scene card
(added in Stage B PR1) will point to the records stored here.

## Storage doctrine

| Asset type | Where it lives |
|---|---|
| `omni_generation_record.json` files (metadata only) | This repo |
| Generated video/image binaries | External DVC-style storage (not yet configured) |
| Selected element refs (small descriptors) | This repo or Git LFS |

**Do not commit large generated binaries here.**
Output file paths are tracked inside `omni_generation_record` JSON records;
the binaries themselves will move to external storage in a later phase.
