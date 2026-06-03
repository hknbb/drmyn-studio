# Scene Continuity System (Production System v2)

End-to-end method for producing Kling Omni (O3) scenes with reliable multi-shot
continuity and no character-clone artifacts. This is the canonical path; new scenes
follow it from the start.

## Canonical pipeline

```
screenplay
  → scene_beat_plan.yaml        (semantic beats; optional figures[] per beat)
  → dialogue_beats.yaml         (lines mapped to beats + speaker @aliases)
  → omni_clip_planner.py        (deterministic packer: beats → shots → clips)
  → omni_clip_plan.yaml + manifests/CLIP_*.yaml   (CLIP = one Kling Omni job, ≤15s, ≤6 shots)
  → scene_continuity_ledger.yaml (inter-clip hand-off: camera + action + screen direction)
  → KlingOmniAdapter.generate_from_clip_manifest()  → O3 multi-shot prompt
  → external Kling generation → video_takes → selected_take → scene_clip_map.csv
```

- **Multi-shot WITHIN a clip** = `omni_clip_manifest.shots[]` (one Kling generation).
- **Continuity BETWEEN clips** = `scene_continuity_ledger.clip_chain[]`.

## Kling Omni (O3) multi-shot prompt rules

Calibrated to the official Kling VIDEO 3.0 Omni guide (see
`model_guidance_snapshots/kling/…_kling_omni_video_best_available.yaml`):

- Single generation: **≤ 6 shots (cuts), ≤ 15s total**; a shot may be **2–15s** (2s cutaways are valid).
- **Format A (silent):** `Shot N (Xs): <framing>. <action + @Element + "Cut to…">.`
- **Format B (native audio):** `[MM:SS – MM:SS] <shot>: @Element <action>. Audio: <cue>.` with inline dialogue `— Name: "…"`.
- **Describe action and camera, not appearance** — identity/wardrobe/look are carried by the attached `@elements`.
- Use linking words ("continuing", "immediately") and consistent screen direction across cuts.
- Enforced by `validate_omni_clip_manifest` (≤6 shots, sum==total) and the golden test `tests/agents/test_prompt_golden_format.py`.

## Anti-clone: one figure ⇒ one alias

Kling collapses two distinct figures sharing a description into one (or clones them).
Rule: **every distinct on-screen figure gets its own `@alias`.** A base character (e.g.
C10) appearing as two figures uses two aliases (`@C10_HOLDER`, `@C10_CARRIER`), each
with a `distinguishing_detail`.

- Authored in `scene_beat_plan.source_beats[].figures[]` / `omni_clip_manifest.shots[].figures[]`.
- Enforced by `scripts/validators/validate_figure_roster.py` (one alias ↔ one figure/role;
  distinct aliases for same base; aliases must be bound; no alias reused in a shot).
- The adapter attaches figure aliases directly (never collapsed by element_id), and the
  prompt enumerates the exact figures + a "no additional/duplicated people" negative.

## Inter-clip continuity ledger

`scene_continuity_ledger.yaml` chains the scene's clips in order and declares each clip's
`entry_state` / `exit_state` (summary, key_positions, props_state, action_state,
camera_state, screen_direction). `validate_scene_continuity_ledger.py` checks the chain
matches the clip plan and that screen direction / shared-subject positions stay continuous
across each cut (180-degree rule). The adapter injects this hand-off into the prompt
("Continue from previous clip…", "End state for next clip…").

## Element references: four-view scale+angle (v3) + look sheet

- Character hero = **Midjourney 8.1**; 4-view expansion + all non-character elements = **ChatGPT Images 2**.
- `gpt_images_perspective_pack` policy **`four_view_scale_angle_v3`**: `full_body_front`,
  `three_quarter_waist`, `close_portrait_front`, `profile_full` — scale ladder + profile for a
  3D identity lock that does not crop. (`perspective_qc_report` and
  `kling_element_reference_record` accept these names; QC already accepts 3 or 4 views.)
- **`character_look_sheet`** captures full-body build/height/physical + head-to-toe wardrobe
  (top, bottom, footwear, outerwear, accessories) + palette, so scale views never invent or crop garments.

## Locations: cinematic width

ChatGPT Images 2 rooms tend to render narrow/box-like. Location packs must include a WIDE
establishing prompt at **16:9 or 2.39:1** with depth/lens cues and explicit **actor blocking /
coverage space** (floor + negative space). Soft-checked by
`scripts/validators/validate_location_framing.py`.

## Local media archive (local-only)

External image/video binaries are filed by `scripts/archive_media.py` into a git-ignored
`archive/<project>/<scene|_elements>/<element>/stage{1,2,3}/{images|video}/…` tree and
registered in a metadata-only `local_media_index` under `evidence/`. Binaries are never
committed (`repo_binary_committed: false`).

## Non-destructive versioning

Change = new `V00N`; the old record is **not deleted** — set `status: deprecated`, add a
`continuity_note`, and (where the schema allows) a `superseded_by` pointer.

## Model guidance

The engine reads model capabilities/rules from the model guidance snapshot; it is
version-agnostic. Current model: **Kling 3.0 Omni / O3**. Update the snapshot (not the
adapter) when the model changes.

## Status / open items

- Prompt generation is canonical via `generate_from_clip_manifest`. The legacy storyboard →
  `shot_list_omni` → `generate()` path is **pending a decouple/removal decision** (large blast
  radius: 33 files / 255 refs) — do not build new scenes on it.
- Scene teardown + rebuild of SC0001/SC0014 under this system is a separate, operator-gated step
  (irreversible deletes; requires operator-produced media + real QC scores).
