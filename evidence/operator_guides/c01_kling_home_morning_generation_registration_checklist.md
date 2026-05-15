# C01 Kling Home Morning Generation Registration Checklist

## Status (2026-05-15)
**PAUSED — v01 prompt deprecated. Do not run external Kling Omni 3 generation
against `prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v01.yaml`.**

The repo workflow now requires every required element for a shot to pass the
full element pipeline (Midjourney hero → GPT Images 2 perspective pack →
`kling_element_reference.yaml` → `element_binding` status `created` or higher)
before any Kling Omni 3 prompt may be synthesized. The v01 draft was authored
before LOC001 (Vale Residence kitchen passage sub-area) and PROP003 (Vardova
skyline photo frame) reached that bar.

This checklist will resume against `…__v02.yaml` after the following PRs land:
- **PR-C:** LOC001 kitchen_passage backfill (MJ prompt record, GPT Images 2
  perspective pack, `kling_element_reference.yaml`, element_binding update).
- **PR-D:** PROP003 backfill (`kling_element_reference.yaml`, element_binding
  promote from `planned` to `created`).
- **PR-E:** `visual_dev/omni_sets/SC0001/shot_element_manifests/SH001.yaml`
  manifest, validator gate pass, v02 prompt regenerated through the adapter.

## Purpose (resumes for v02)
Operator checklist for registering the first external Kling Omni 3 Home Morning
draft clip output after prompt generation.

## Source Prompt (v02 — pending)
- Prompt record:
  `prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v02.yaml`
  *(not yet generated; will be authored by the Kling Omni adapter once the
  shot element manifest gate passes)*
- Clip ID:
  `CLIP_SC0001_HOME_MORNING_DRAFT_01`
- Continuity language:
  selected Stage 4 perspective set

## Element Registration Requirement (replaces prior Alias / Context Taxonomy)
Every element referenced by the shot must be a fully registered Kling Omni
element before it appears in the v02 prompt. There is no longer a
"text-described scene context" or "prompt-described action" path for elements
the script actually requires the viewer to see.

The v02 prompt must reference all required elements **only through their
registered `@alias`** values. Canonical repo IDs (`C01`, `LOC001`,
`LOC001_KITCHEN_PASSAGE`, `PROP003`) and raw human-language names (`Nadia`,
`Vale Residence`, `Vardova`) must not leak into `prompt_text`.

Expected required elements for SC0001 SH001 once backfill completes:

| Repo element | Registered Kling alias | Role |
|---|---|---|
| C01 (character look composite, home morning) | `@Nadia` (platform), `@C01_HOME_MORNING` (repo canonical) | primary_subject |
| LOC001 kitchen passage (location sub-area) | `@ValeResidenceKitchenPassage` | attached_location |
| PROP003 (tilted Vardova skyline photo frame) | `@VardovaFrame` | attached_prop |

Truly environmental flourishes that the script does not require the viewer to
identify (e.g., ambient practical lighting palette notes) may be enumerated in
`environmental_only_allowed_ids` inside the shot element manifest — that field
is a tightly scoped exception, not a fallback for unfinished element work.

## Registration Preconditions (apply to v02 generation)
- Shot element manifest for SC0001 SH001 is merged and validator passes
  `gate_status: all_elements_ready`.
- All required elements (C01, LOC001 kitchen_passage, PROP003) have
  `kling_element_reference.yaml` at status `review` or higher.
- All required element bindings in
  `visual_dev/omni_sets/SC0001/element_bindings.yaml` are at status `created`
  or higher (no `planned`).
- v02 prompt draft is merged and validator passes.
- Kling output exists externally.
- Output filename and storage path are operator-confirmed.
- Output is not committed as binary.
- Output is not treated as materialized/final.
- QC has not yet been populated.

## Allowed Registration Changes
- Add or update external output metadata reference.
- Record `external://local_manual/...` output path.
- Keep `repo_binary_committed: false`.
- Mark QC as pending.
- Keep lifecycle draft/review only.

## Forbidden
- No video/audio/image binary commit.
- No materialized output registration.
- No lifecycle promotion to approved/locked/materialized.
- No final human QC verdicts or lifecycle-facing QC decisions in the registration PR.
- If `video_takes.yaml` is written via the `review-video-takes` flow, keep schema-required
  `quality_scores` populated as draft review metadata only (not as final approval evidence).
- No prompt rewrite in the registration PR.
- No canonical terminology for the selected Stage 4 perspective set.
- No registration against v01 (deprecated).

## Expected Follow-up PRs (resume after v02 exists)
1. Output registration PR.
2. Kling clip QC scaffold/update PR.
3. Human review / revision decision PR.
4. Only later: lifecycle promotion if explicitly approved.

## Validation
- `python scripts/validate_production_records.py --repo-root .`
- `python scripts/validate_prompt_records.py --repo-root .`
