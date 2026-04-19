# post — Post-Production Working Tree

Introduced in **Stage B PR2** as folder scaffolding only.
All sub-folders are empty (`.gitkeep` only) until post-production begins.

## Sub-folders

```
post/
  dialogue/
    SC0001/ … SC0120/   ← per-scene dialogue/lipsync working files
  edit/
    proxies/            ← low-res proxy edits for offline review
    offline/            ← offline editorial project files
    online/             ← online / conform project files
  color/
    luts/               ← LUT files for color grading
    grades/             ← per-scene grade exports and looks
  sound/
    sfx/                ← sound effects library and scene-specific SFX
    music/              ← score stems and music assets
    mixes/              ← final and interim mix exports
```

## Storage doctrine

| Asset type | Where it lives |
|---|---|
| Small descriptor files, YAML metadata, lipsync records | This repo |
| Large audio/video render outputs | External DVC-style storage (not yet configured) |
| LUT files (typically small, < 1 MB) | This repo directly |
| Project files (Resolve, Avid, Premiere) | External storage; paths logged in records |

**Do not commit large audio/video binaries directly.**
The `lipsync_record` schema (added in Stage B PR1) tracks
per-scene lipsync provenance; records go in `post/dialogue/SC####/`.
