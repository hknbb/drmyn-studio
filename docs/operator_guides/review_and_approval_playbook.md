# Review And Approval Playbook

Production changes that affect lifecycle state are human-gated. Agents can
write metadata suggestions and review records, but approval and promotion
happen through PR review.

## Human Gates

- Prompt records move from `draft` only through reviewed changes.
- Element packs move through `metadata_only`, `seeded`, `approved`, and
  `locked` by human PR.
- Storyboard selection is a human decision and is not changed by Batch 5.85.
- Clip locking is not active until later video batches.

## Agent Limits

Batch 5.85 guidance must not:

- Update `pack_status`
- Update `canon_lock`
- Update `approved`
- Update `locked`
- Update `selected_option`
- Modify `scene_card.yaml`
- Modify `pack_manifest.yaml`
- Run external generation tools

## Review Notes

When preparing image review, write text notes that identify:

- Source prompt id
- Candidate image paths or external storage refs
- Main strengths and failures
- Any prompt repair needed
- Any clearance concern

The metadata review pass can then produce review records without touching
lifecycle state directly.
