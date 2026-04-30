# Midjourney Prompt Guidance — Research Log

**Batch:** 0.25
**Purpose:** Human-curated source log for the Midjourney model guide.
This file records which official sources were consulted, what was found,
and what rules were extracted. It is the evidence base for `docs/model_guides/midjourney.yaml`.

**Status:** Seed skeleton — to be filled by operator before running Batch 4 adapters.
`docs/model_guides/midjourney.yaml` must not be marked `confidence: high` until
at least one source in this log is marked `human_verified: true`.

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

### Source 1 — Official Documentation
- **URL:** https://docs.midjourney.com/docs/prompts
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false *(operator sets to true after reading)*
- **Notes:** Main prompt reference. Covers basic prompt structure, parameters.

### Source 2 — Parameter Reference
- **URL:** https://docs.midjourney.com/docs/parameter-list
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Full `--` parameter list including `--no` (negative prompt), `--ar`, `--chaos`, `--s`, `--v`.

### Source 3 — Version Release Notes
- **URL:** https://docs.midjourney.com/docs/versions
- **Source class:** `official_release_notes`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Version changelog. Verify current default version (MJ 6.1 as of early 2026).

---

## Extracted Prompt Rules (Draft)

> ⚠️ These are seed rules only. Operator must verify against current official docs
> before running `--mode refresh-model-guidance` with `confidence: high`.

1. **Subject-first:** Lead with the primary subject and its dominant quality.
   *Source: docs.midjourney.com/docs/prompts*
2. **Compact visual clauses:** Use noun phrases separated by commas, not full sentences.
   Max effective prompt length: ~60–80 words before diminishing returns.
   *Source: docs.midjourney.com/docs/prompts*
3. **Negative prompts via `--no`:** Midjourney does not have a separate negative prompt field.
   Use `--no <term>` at the end of the prompt. `supports_negative_prompt: limited`.
   *Source: docs.midjourney.com/docs/parameter-list*
4. **Aspect ratio `--ar`:** Use `--ar 16:9` for cinematic wide, `--ar 1:1` for square.
   *Source: docs.midjourney.com/docs/parameter-list*
5. **Stylize `--s`:** Controls how strongly Midjourney's aesthetic sense applies.
   Range 0–1000; default 100. High values = more artistic but less literal.
   *Source: docs.midjourney.com/docs/parameter-list*
6. **Chaos `--chaos`:** Range 0–100. Higher = more variation between results.
   Use 0 for reproducibility.
   *Source: docs.midjourney.com/docs/parameter-list*
7. **Seed `--seed`:** Reproducibility. Use same seed + same prompt = similar result.
   `supports_seed: true`.
   *Source: docs.midjourney.com/docs/parameter-list*
8. **No identity consistency across separate jobs:** Midjourney does not natively
   preserve character identity across separate generation jobs.
   `supports_consistency_reference: false`.
   *Source: community knowledge — requires verification against current docs*
9. **Version targeting `--v`:** Always specify `--v 6.1` (or current version) to pin
   output style to a known model version.
   *Source: docs.midjourney.com/docs/versions*
10. **No ChatGPT-style revision:** Midjourney does not support iterative text revision
    of a prior generation via conversation. Each job is standalone.

---

## Do Not Invent / Requires Verification

- Any stylistic shorthand not found in official docs (e.g. "filmic", "cinestill" effects)
- Prompt weighting syntax (`word::2`) — verify current support in MJ 6.x
- `--cref` (character reference) — verify support and format in current docs

---

## Model Version Observed

- **Version string:** Midjourney 6.1 *(as of early 2026 — operator must verify)*
- **Confidence:** low *(placeholder; set to high after operator verification)*

---

## Operator Action Required

Before the Midjourney adapter runs in Batch 4:

1. Visit each source URL above.
2. Fill in `Retrieved at` and `HTTP status`.
3. Set `Human verified: true` if the rule is confirmed in the source.
4. Run: `python scripts/agents/run_pipeline.py --mode refresh-model-guidance --models midjourney --save-snapshot`
5. Update `docs/model_guides/midjourney.yaml` confidence level if sources confirm rules.
