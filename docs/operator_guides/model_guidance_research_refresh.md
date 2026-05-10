# Model Guidance Research Refresh Guide

## Purpose

Before every production prompt generation batch, model guidance snapshots must be
fresh, human-verified, and non-placeholder. This guide explains how to identify
stale snapshots, research the correct current guidance, update snapshot files, and
re-run the gate to confirm readiness.

## When to refresh

Run a research refresh when:
- The pre-batch gate (`validate_model_research_gate.py`) exits with code 1.
- A snapshot's `expires_at` is within 24 hours.
- An adapter returns a `ModelGuidanceResolutionError` about expiry or placeholders.
- A new model version is publicly announced for any target model.
- A prompt generation batch is starting after more than 7 days (Kling Omni) or 14 days (others).

## Workflow

### Step 1 — Run the gate

```bash
python scripts/validators/validate_model_research_gate.py \
  --targets kling_omni_video_best_available \
           chatgpt_image_best_available \
           midjourney_image_best_available \
           nano_banana_best_available
```

Exit 0 = unblocked. Exit 1 = one or more targets need refresh.

### Step 2 — Generate research checklists

When the gate fails, run the refresh operator to get per-target checklists and
snapshot scaffolds:

```bash
# Print checklists to stdout and write scaffold YAMLs:
python scripts/operators/model_guidance_refresh_operator.py \
  --targets <failing_target_1> <failing_target_2> \
  --write-scaffolds

# Or write a markdown report file:
python scripts/operators/model_guidance_refresh_operator.py \
  --report-file refresh_report.md --write-scaffolds
```

The scaffold files are written to `model_guidance_snapshots/<provider>/<timestamp>_<target>_SCAFFOLD.yaml`.
They contain all required fields with `TODO_` placeholders to fill in from research.

### Step 3 — Research each failing target

Follow the per-target research checklist from Step 2. Use only the approved source tiers:

| Tier | Source types | Policy |
|------|-------------|--------|
| **Tier 1 — Official** | `official_docs`, `official_release_notes`, `official_help_center` | Authoritative. Use for all hard constraints and hard rules. |
| **Tier 2 — Verified** | `verified_platform_blog`, reputable API/provider docs | Acceptable for prompt strategy guidance when corroborated by Tier 1. |
| **Community / General Web** | Forum posts, community tip sheets, social media | Low-confidence note ONLY. Must NOT become a hard rule without official corroboration and human review. |

#### Per-model primary sources

**Kling Omni (`kling_omni_video_best_available`)**
- https://kling.ai/quickstart/klingai-element-library-3-user-guide — Element Library, `@` alias usage
- https://docs.magnific.com/api-reference/video/kling-v3-omni/generate-std-video-reference — hard API limits
- https://blog.fal.ai/kling-3-0-prompting-guide/ — cinematic direction, motion intensity, end-state

**Midjourney (`midjourney_image_best_available`)**
- https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version — current version
- https://midjourney.com/updates — release notes

**ChatGPT Image (`chatgpt_image_best_available`)**
- https://help.openai.com/en/articles/9055440 — current image model in ChatGPT
- https://platform.openai.com/docs/guides/images — API parameters

**Nano Banana (`nano_banana_best_available`)**
- https://ai.google.dev/gemini-api/docs/image-generation — API docs
- https://blog.google/products/gemini/prompting-tips-nano-banana-pro — prompting guidance

### Step 4 — Fill in the scaffold

Open the generated `_SCAFFOLD.yaml` file and replace every `TODO_` field with
verified information from research. Key fields:

```yaml
current_default_model: "<fill from official docs>"
latest_available_model: "<fill from official docs>"
best_for_this_task: "<fill from official docs>"
constraints:
  prompt_text_max_chars: <fill if stated in API docs>
  negative_prompt_max_chars: <fill if stated in API docs>
prompting_rules:
  - "<concrete rule from Tier 1 source>"
sources:
  - source_type: official_docs
    title: "<source title>"
    retrieved_at: "<ISO-8601 timestamp>"
    url: "<actual URL consulted>"
human_verified: false  # set to true only after review
```

Remove the `_scaffold_notes` field before committing.

### Step 5 — Rename and commit the snapshot

Rename `_SCAFFOLD.yaml` to remove the `_SCAFFOLD` suffix:

```
model_guidance_snapshots/<provider>/<timestamp>_<target>.yaml
```

Set `human_verified: true` only after you have reviewed the content.

Commit the snapshot with a message explaining what changed and why.

### Step 6 — Re-run the gate

```bash
python scripts/validators/validate_model_research_gate.py
```

All targets should now exit 0. If not, repeat from Step 3 for remaining failures.

## Hard boundaries

- Do not add live internet calls to adapters, the critic, or validators.
- Do not generate prompts before the gate passes.
- Do not set `human_verified: true` on scaffolds or on research done by an automated agent
  without human operator review.
- Do not commit `_SCAFFOLD.yaml` files — they are temporary working files.
- No API keys, browser tokens, or credentials belong in snapshot files or repo files.

## Freshness policy

| Model target | Max age |
|---|---|
| `kling_omni_video_best_available` | 7 days |
| `midjourney_image_best_available` | 14 days |
| `chatgpt_image_best_available` | 14 days |
| `nano_banana_best_available` | 14 days |
