# Kling Omni Generation Playbook

Batch 8 activates metadata-only Kling Omni prompt drafting. It does not run
Kling, upload assets, create video takes, review video, or lock clips.

## Activation Gate

Do not generate Kling Omni prompt metadata until all of the following are true:

- Required element packs are locked by human PR.
- Storyboard direction is selected by the approved workflow.
- `scene_card.shot_list_omni` is non-empty after human PR application.
- `scene_card.omni_set_ref` is present.
- Kling model guidance is active and recently reviewed.

The adapter may be run with:

```bash
python scripts/agents/run_pipeline.py \
  --mode generate-kling-omni-prompts \
  --scene-id SC0001
```

## Current Safe Action

If any activation gate is missing, treat the task as blocked. Do not use
`shot_list_omni_suggestion.yaml` alone as an unlock; a human must apply the
shot list to `scene_card.yaml` through PR first.

## Storage Safety

Do not commit `.mp4`, `.mov`, or other video binaries in this phase. Use the
future approved external storage reference workflow.

Batch 8 writes prompt metadata only. `video_takes.yaml`, `selected_take.yaml`,
and `evidence/scene_clip_map.csv` remain out of scope.
