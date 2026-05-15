# C01 Kling Home Morning Generation Registration Checklist

## Purpose
Operator checklist for registering the first external Kling Omni 3 Home Morning draft clip output after prompt generation.

## Source Prompt
- Prompt record:
  `prompts/draft/SC0001__omni-kling-omni3-home-morning-tilted-frame__v01.yaml`
- Clip ID:
  `CLIP_SC0001_HOME_MORNING_DRAFT_01`
- Active character element:
  repo canonical alias `@C01_HOME_MORNING`, resolved for the Kling Web UI through
  `visual_dev/omni_sets/SC0001/element_bindings.yaml` as `@Nadia`
- Continuity language:
  selected Stage 4 perspective set

## Alias / Context Taxonomy
- `@C01_HOME_MORNING` is the repo canonical audit alias for the C01 Home Morning
  look composite. It is not necessarily the literal Kling UI element name.
- For this draft, the operator selects the existing Kling UI character element
  `@Nadia`, which is bound to C01 in `element_bindings.yaml`.
- The Vale Residence kitchen passage (`LOC001`) is text-described scene context
  for this draft. Do not treat `@ValeResidenceKitchenPassage` as an attached
  location element unless a later reviewed prompt explicitly attaches it.
- The tilted Vardova skyline photo frame (`PROP003`) is a required visual cue
  described in the prompt. Do not treat it as a separately attached Kling prop
  element in this draft.

## Registration Preconditions
- Alias/context/cue taxonomy patch is merged before any Kling render attempt.
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
