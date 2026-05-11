# Nano Banana Reference Source Audit

## Canonical Source Layer
- Character view plans: `visual_dev/elements/characters/*/element_view_plan.yaml`
- Location view plans: `visual_dev/elements/locations/*/element_view_plan.yaml`
- Prop view plans: `visual_dev/elements/props/*/element_view_plan.yaml`
- Wardrobe view plans: `visual_dev/elements/wardrobe/*/element_view_plan.yaml`

Each `views[]` item is considered usable only when:
- `status == complete`
- `canonical_asset_path` is present and non-empty

## Repo Policy Caps (Deterministic)
- `character_reference_refs`: max `5`
- `object_reference_refs`: max `6`

These are repository discipline caps, independent from provider technical limits.

## Deterministic Prioritization
- Element-type order: `character > location > prop > wardrobe`
- Within each element type: lexicographic by `element_id`
- Within each view plan: file order of `views[]`

## Integration Decision
- Implemented via `SourceContextAgent` extension.
- `SourceContext.element_reference_assets` now carries:
  - `character`: list of canonical asset paths
  - `object`: list of canonical asset paths

This is then propagated into `NeutralBrief` and consumed by `NanaBananaAdapter`.
