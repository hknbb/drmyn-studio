## Summary

Implements A6.1 only.

Adds the model guidance resolver used by later prompt/adapter work to resolve current model guidance from validated snapshot YAML files.

## Files Changed (A6.1 scope)

- `scripts/agents/model_guidance_resolver.py`
- `tests/agents/__init__.py`
- `tests/agents/test_model_guidance_resolver.py`

## Resolver Behavior

- Loads snapshot YAML files from `model_guidance_snapshots/<provider>/*.yaml`
- Validates snapshots against `schemas/model_guidance_snapshot.schema.json`
- Filters by `internal_model_target`
- Rejects missing, expired, unverified, schema-invalid, or placeholder-containing snapshots
- Selects the newest valid `observed_at` when multiple valid snapshots exist
- Resolves feature-specific model names via `feature_required_model[required_feature]`
- Returns provider, provider surface, resolved model name, resolved role, expiry metadata, prompting rules, capabilities, and constraints
- Does not modify adapters
- Does not create snapshot YAML files
- Does not modify `prompt_record.schema.json`

## Test Plan

```bash
python -m pytest tests/test_model_guidance_snapshot_schema.py tests/agents/test_model_guidance_resolver.py -q
```

Result: 24 resolver tests passing, plus A6.0 schema tests passing.

## Scope Guard

No changes to:

* `model_guidance_snapshots/`
* `scripts/agents/adapters/`
* `schemas/prompt_record.schema.json`
* `prompts/`
* `planning/`
* `visual_dev/`
* `evidence/`
* `assets/`

## Next Step

After A6.1 merges, proceed to A6.2 snapshot records.
A7 adapter work remains blocked until A6.1 + A6.2 + A6.3 are complete.
