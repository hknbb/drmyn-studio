## Summary

Renames the Kling internal model target from generic `kling_video_best_available` to version-free Omni-family `kling_omni_video_best_available`.

This prevents the guidance resolver from confusing generic Kling Video T2V/I2V targets with the project's intended Kling Omni element-based production pipeline.

## Why

The project targets Kling Omni-family capabilities:
- Element Library
- Element Reference
- Video Element Reference
- Native Audio
- Element Voice Control
- Multi-shot

The internal target identifies the Omni family only. It does not encode an Omni version number.

## Changed Files

- `schemas/model_guidance_snapshot.schema.json`
- `scripts/agents/model_guidance_resolver.py`
- `tests/test_model_guidance_snapshot_schema.py`
- `tests/agents/test_model_guidance_resolver.py`

## Validation

- `kling_omni_video_best_available` is accepted.
- `kling_video_best_available` is rejected.
- No `kling_omni_3_*` internal target introduced.
- No `VIDEO 3.0 Omni` hardcoded in resolver/adapters/schema defaults.
- No `model_guidance_snapshots/` created.
- No adapters modified.
- No `prompt_record.schema.json` changes.

## Test Plan

```bash
python -m pytest tests/test_model_guidance_snapshot_schema.py tests/agents/test_model_guidance_resolver.py -q
```

Result: 55 tests passing.

## Scope Guard

No changes to:

* `model_guidance_snapshots/`
* `scripts/agents/adapters/`
* `schemas/prompt_record.schema.json`
* `prompts/`
* `planning/scenes/`
* `visual_dev/`
* `evidence/`
* `assets/`

## Next Step

After this PR merges, A6.2 snapshot records can be authored using `kling_omni_video_best_available`.
