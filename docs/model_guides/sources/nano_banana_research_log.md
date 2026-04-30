# Nano Banana Prompt Guidance — Research Log

**Batch:** 0.25
**Purpose:** Human-curated source log for the Nano Banana model guide.
This file records which official sources were consulted, what was found,
and what rules were extracted. It is the evidence base for `docs/model_guides/nano_banana.yaml`.

**Status:** Seed skeleton — to be filled by operator before running Batch 4 adapters.

**Key capability (capability matrix):**
`supports_identity_consistency: true` — designed for generating identity-consistent
character variations. This is the primary differentiator from Midjourney.
`supports_variation_prompting: true`.

---

## Approved Source Classes

| Class | Allowed |
|---|---|
| `official_docs` | ✅ |
| `official_release_notes` | ✅ |
| `official_help_center` | ✅ |
| `verified_platform_blog` | ✅ |
| `forum_threads` | ❌ blocked |
| `prompt_hack_blogs` | ❌ blocked |
| `unsourced_social_media` | ❌ blocked |
| `paid_prompt_packs` | ❌ blocked |

---

## Sources Consulted

### Source 1 — Official Platform Documentation
- **URL:** *(operator fills in — find official Nano Banana docs URL)*
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Main prompt reference. Focus on identity consistency and variation features.

### Source 2 — Release Notes / Blog
- **URL:** *(operator fills in)*
- **Source class:** `official_release_notes`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Version history and capability additions.

---

## Extracted Prompt Rules (Draft)

> ⚠️ Seed rules only. Operator must verify before `confidence: high`.
> Note: Nano Banana has less public documentation than Midjourney or OpenAI.
> All rules below marked with confidence level.

1. **Identity consistency mode:** Nano Banana's primary feature is generating
   variations of a character while preserving identity (face, body type, features).
   Use a reference image + prompt for consistent character reproduction across scenes.
   `supports_identity_consistency: true`.
   *Confidence: medium — verify exact workflow in official docs*
2. **Variation prompting:** Can generate multiple variations from a single brief.
   `supports_variation_prompting: true`.
   *Confidence: medium*
3. **Negative prompt support:** Nano Banana supports negative prompts as a parameter.
   `supports_negative_prompt: true`.
   *Confidence: medium — verify parameter name and format in official docs*
4. **No seed parameter:** Seed-based reproducibility not confirmed.
   `supports_seed: false` (pending verification).
   *Confidence: low — needs official source*
5. **Prompt structure:** *(operator fills in after reading official docs)*
6. **Character reference workflow:** *(operator fills in — how to provide reference image)*

---

## Do Not Invent / Requires Verification

- Exact parameter names (negative prompt field name, variation count parameter)
- Whether seed is supported
- Maximum prompt length
- Current model version number
- Character reference image format requirements

---

## Model Version Observed

- **Version string:** *(operator fills in)*
- **Confidence:** low *(placeholder)*

---

## Research Priority

> Nano Banana has less publicly available documentation than Midjourney or OpenAI.
> The operator should search for official documentation at the Nano Banana platform
> before running Batch 4. If official docs are insufficient, mark confidence as
> `medium` and flag `do_not_use_without_verification` for any rules not from
> `official_docs` or `official_release_notes`.

---

## Operator Action Required

Before the Nano Banana adapter runs in Batch 4:

1. Find and visit official Nano Banana documentation.
2. Fill in source URLs, `Retrieved at`, `HTTP status`.
3. Verify `supports_identity_consistency: true` and note the workflow.
4. Verify `supports_negative_prompt: true` and note the parameter name.
5. Run: `python scripts/agents/run_pipeline.py --mode refresh-model-guidance --models nano-banana --save-snapshot`
6. Update `docs/model_guides/nano_banana.yaml` confidence level.
