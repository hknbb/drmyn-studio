# Omni Prompt Component Model

This document defines how Kling Omni `prompt_text` is composed from structured components rather than free-form single-block text.

## Canonical component order

1. `goal`
2. `duration_format`
3. `scene_context`
4. `active_elements`
5. `shot_plan`
6. `action_timeline`
7. `camera_grammar`
8. `audio_plan`
9. `negative_constraints`
10. `style_color`
11. `expected_outcome`
12. `retry_rule`

## Component to source mapping

- `goal` -> `planning/scenes/SC####/scene_card.yaml` (`purpose`) + beat role
- `duration_format` -> `planning/scenes/SC####/manifests/*_manifest.yaml` (`total_duration_seconds`)
- `scene_context` -> `scene_card` + `planning/locations/*.yaml`
- `active_elements` -> `visual_dev/omni_sets/SC####/element_bindings.yaml` + `required_element_ids`
- `shot_plan` -> `omni_clip_manifest.shots[]`
- `action_timeline` -> `shots[].duration_seconds` + `shots[].prompt_action`
- `camera_grammar` -> `shots[].camera`
- `audio_plan` -> `kling_native_audio` + `planning/scenes/SC####/dialogue_beats.yaml`
- `negative_constraints` -> model-guide defaults + prompt record negative constraints
- `style_color` -> `planning/aesthetic_bible.yaml` + shot lighting
- `expected_outcome` -> `prompt_record.expected_output`
- `retry_rule` -> QC record or next-pass note

## Rendering rule

The adapter renders `prompt_text` in this fixed order. Component ordering is not randomized.

## Policy constraints

- Canonical planning IDs must not leak into `prompt_text`.
- `required_element_aliases` must be preserved and visible in prompt text.
- Apply hard guard when prompt character limits are exceeded.
- Do not invent new story facts.

## Variant compatibility

The same component skeleton must work across:

- `safe`
- `creative`
- `aggressive`

Variants may change expression intensity, not source-grounded facts.
