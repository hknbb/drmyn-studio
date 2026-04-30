# Kling Omni Generation Playbook

Batch 8 activates metadata-only Kling Omni prompt drafting. Batch 8.5 records
metadata-only review of externally generated Kling takes. The repo still does
not run Kling, upload assets, copy video binaries, or lock clips.

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

## Video Take Handoff

After external Kling generation, collect platform/storage refs in a YAML or JSON
handoff file and write human review notes. Then run:

```bash
python scripts/agents/run_pipeline.py \
  --mode review-video-takes \
  --scene-id SC0001 \
  --prompt-id SC0001__omni-kling-omni__v01 \
  --takes-metadata handoff/SC0001_takes.yaml \
  --review-notes evidence/video_reviews/SC0001_review_notes.md
```

The command writes `video_takes.yaml` and review metadata only. If prompt
revision is needed, it may also write a corrected brief under
`evidence/prompt_reviews/`.

## Storage Safety

Do not commit `.mp4`, `.mov`, `.mkv`, `.wav`, or other video binaries in this
phase. Store only `platform_asset_ref` and `external_storage_ref` metadata.

Batch 8.5 may write `video_takes.yaml`; `selected_take.yaml` and
`evidence/scene_clip_map.csv` remain Batch 9 outputs.

## Final Clip Locking

When `video_takes.yaml` has exactly one selected take, lock the final scene clip
metadata:

```bash
python scripts/agents/run_pipeline.py \
  --mode lock-scene-clip \
  --scene-id SC0001 \
  --locked-by human_operator \
  --locked-at 2026-04-30T00:00:00Z
```

This writes `selected_take.yaml` and `evidence/scene_clip_map.csv` only. It
does not modify `video_takes.yaml` and does not create proxy/video binaries.
