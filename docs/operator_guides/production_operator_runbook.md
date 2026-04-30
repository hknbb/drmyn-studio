# Production Operator Runbook

Batch 5.85 adds a human-facing guidance layer. The repo can recommend the next
safe production task, but the operator still performs external image/video work
manually and all lifecycle promotion remains human-gated.

## Start Here

Run the guidance helper:

```bash
python scripts/agents/run_pipeline.py --mode operator-next-step --repo-root .
```

The helper reads existing metadata and prints:

- current_task
- scene_id
- open_files
- do_steps
- expected_outputs
- next_command_or_manual_step
- safety_warnings
- blocked_reason when blocked

It does not generate prompts, run Midjourney, run ChatGPT Image, run Nano
Banana, run Kling, write scene cards, update pack manifests, or promote
lifecycle fields.

Direct helper usage remains available for debugging:

```bash
python scripts/agents/operator_next_step.py --repo-root .
```

## Production Order

1. T2I image generation from existing prompt drafts.
2. Image review preparation when candidates exist but review notes are missing.
3. Metadata-only image review once candidates and notes exist.
4. Storyboard option selection when `storyboard_options.yaml` exists and
   `selected_option` is still null.
5. Kling Omni video generation later, after Batch 8 activates that phase.

## Safety Rules

- Do not commit image or video binaries unless the storage policy explicitly
  allows the asset class and Git LFS is configured for it.
- Do not edit `pack_status`, `canon_lock`, `approved`, `locked`, or
  `selected_option` as part of Batch 5.85.
- Do not edit `scene_card.yaml` or `pack_manifest.yaml` from operator guidance.
- Treat external generation tools as manual operator actions.
- Use PR review for approval and lifecycle promotion.

## Related Playbooks

- `docs/operator_guides/t2i_image_generation_playbook.md`
- `docs/operator_guides/storyboard_selection_playbook.md`
- `docs/operator_guides/kling_omni_generation_playbook.md`
- `docs/operator_guides/review_and_approval_playbook.md`
- `docs/methodology/storage_policy.md`
