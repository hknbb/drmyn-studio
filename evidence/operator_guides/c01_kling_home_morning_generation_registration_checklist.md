# C01 Kling Home Morning Generation Registration Checklist

## Status (2026-05-15)
READY FOR V02 DRAFT GENERATION.

Use only:
`prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v02.yaml`

Do not use:
`prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v01.yaml` (deprecated)

Backfill checkpoint now recorded:
- LOC001 kitchen_passage `kling_element_reference.yaml`: `status: review`
- PROP003 `kling_element_reference.yaml`: `status: review`
- PROP003 binding: `planned -> created`
- SC0001 SH001 shot manifest: `gate_status: all_elements_ready`

## Purpose
Operator checklist for registering the first external Kling Omni 3 Home Morning
draft clip output after prompt generation.

## Source Prompt (v02)
- Prompt record:
  `prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v02.yaml`
- Clip ID:
  `CLIP_SC0001_HOME_MORNING_DRAFT_01`
- Continuity language:
  selected Stage 4 perspective set

## Element Registration Requirement
Every required shot element must be attached as a registered Kling element.
No fallback text-context path is allowed for required elements.

Expected attached aliases for SC0001 SH001:
- `@Nadia`
- `@ValeResidenceKitchenPassage`
- `@VardovaFrame`

Canonical IDs (`C01`, `LOC001`, `PROP003`) must stay in metadata fields only,
not in `prompt_text`.

## Registration Preconditions
- Shot manifest gate is `all_elements_ready`.
- All required `kling_element_reference.yaml` records are `review` or better.
- All required scene bindings are `created` or better.
- v02 prompt validates.
- Kling output exists externally.
- Output path is operator-confirmed.
- Output is not committed as binary.
- QC remains draft/pending in registration PR.

## Allowed Registration Changes
- Add/update external output metadata references.
- Record `external://local_manual/...` output path.
- Keep `repo_binary_committed: false`.
- Keep lifecycle in draft/review scope.

## Forbidden
- No video/audio/image binary commit.
- No materialized output registration.
- No lifecycle promotion to approved/locked/materialized.
- No final human QC verdicts in registration PR.
- No registration against v01.

## Expected Follow-up PRs
1. `chore(c01): register first Kling Home Morning draft output metadata`
2. Kling clip QC scaffold/update PR
3. Human review/revision decision PR
4. Lifecycle promotion PR (only if explicitly approved)

## Validation
- `python scripts/validate_production_records.py --repo-root .`
- `python scripts/validate_prompt_records.py --repo-root .`
