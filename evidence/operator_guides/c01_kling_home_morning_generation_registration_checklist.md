# C01 Kling Home Morning Generation Registration Checklist

## Purpose
Operator checklist for registering the first external Kling Omni 3 Home Morning draft clip output after prompt generation.

## Source Prompt
- Prompt record:
  `prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v01.yaml`
- Clip ID:
  `CLIP_SC0001_HOME_MORNING_DRAFT_01`
- Active character element:
  `@C01_HOME_MORNING`
- Continuity language:
  selected Stage 4 perspective set

## Registration Preconditions
- Prompt draft is merged.
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
- No QC score population in the registration PR.
- No prompt rewrite in the registration PR.
- No canonical terminology for the selected Stage 4 perspective set.

## Expected Follow-up PRs
1. Output registration PR.
2. Kling clip QC scaffold/update PR.
3. Human review / revision decision PR.
4. Only later: lifecycle promotion if explicitly approved.

## Validation
- `python scripts/validate_production_records.py --repo-root .`
- `python scripts/validate_prompt_records.py --repo-root .`
