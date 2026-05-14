# C01 Kling Prompt Readiness Final Checklist

## Purpose
Final operator checklist before generating Kling Omni 3 prompts or video outputs for C01 Nadia.

## Preconditions
- C01 FRONT HERO LOCK is registered.
- Stage 4 GPT Images 2 perspective outputs are externally registered.
- All four Stage 4 perspectives passed QC threshold.
- Human selection gate completed with selected Stage 4 perspective set.
- `kling_element_reference.yaml` approval gate is ready.
- HOME_MORNING and NIGHT_TIRED Kling look elements reference `GPTIMG2_C01_PERSPECTIVE_PACK_V001`.

## Allowed Next Work
- Prepare Kling Omni 3 prompt drafts.
- Reference selected Stage 4 perspective set as character continuity support.
- Use look-specific aliases:
  - `@C01_HOME_MORNING`
  - `@C01_NIGHT_TIRED`

## Forbidden In This Checklist PR
- No generated Kling video output.
- No image/video/audio binaries.
- No lifecycle promotion to approved/locked/materialized.
- No QC score mutation.
- No canonical_images mutation.
- No schema or validator edits.

## Required Language
Use “selected Stage 4 perspective set”.
Do not call the set canonical unless a future schema-supported canonicalization PR explicitly permits it.

## Validation
- `python scripts/validate_production_records.py --repo-root .`
- `python scripts/validate_prompt_records.py --repo-root .`
