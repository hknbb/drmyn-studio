# Storyboard Selection Playbook

Use this when `operator_next_step.py` reports `current_task:
storyboard_selection`.

## Inputs

- `visual_dev/storyboards/SC####/storyboard_options.yaml`
- Scene card and scene excerpt listed in `source_refs`

## Manual Steps

1. Open the listed storyboard options file.
2. Compare all options by purpose, camera angle, framing, movement, lighting,
   source field, and status.
3. Prefer options marked `candidate`.
4. Treat `blocked` and `evidence_thin` options as requiring human judgment or a
   separate source-fix PR.
5. After the human selection is recorded by the approved workflow, run the
   shot list Omni suggestion helper for the scene.

```bash
python scripts/agents/run_pipeline.py \
  --mode generate-shot-list-omni-suggestion \
  --scene-id SC0001
```

## Expected Outputs

- A human decision ready for a later PR.
- `shot_list_omni_suggestion.yaml` after a selected storyboard option exists.
- No direct edit to `selected_option` from the guidance helper.
- No direct edit to `scene_card.yaml` from the suggestion helper.
- No storyboard image or video binaries from this batch.
