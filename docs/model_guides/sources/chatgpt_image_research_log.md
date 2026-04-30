# ChatGPT Image Prompt Guidance — Research Log

**Batch:** 0.25
**Purpose:** Human-curated source log for the ChatGPT Image model guide.
This file records which official sources were consulted, what was found,
and what rules were extracted. It is the evidence base for `docs/model_guides/chatgpt_image.yaml`.

**Status:** Seed skeleton — to be filled by operator before running Batch 4 adapters.

**Key constraint (capability matrix):**
`supports_negative_prompt: false` — constraints must be embedded in the positive prompt.
All adapters must set `generation_params.constraint_strategy: embedded_positive_constraints`.
The Critic must NOT require a `negative_prompt` field for this model.

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

### Source 1 — OpenAI Image Generation Docs
- **URL:** https://platform.openai.com/docs/guides/images
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Official image generation API guide. Covers prompt structure, model selection.

### Source 2 — OpenAI ChatGPT Image Release Notes
- **URL:** https://openai.com/blog/chatgpt-image-1 *(verify current URL)*
- **Source class:** `official_release_notes`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Release announcement for GPT-4o image generation capabilities.

### Source 3 — OpenAI Help Center
- **URL:** https://help.openai.com/en/articles/ *(find relevant image generation article)*
- **Source class:** `official_help_center`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** User-facing help content about image generation best practices.

---

## Extracted Prompt Rules (Draft)

> ⚠️ Seed rules only. Operator must verify before `confidence: high`.

1. **Natural language task framing:** ChatGPT Image responds well to full sentences
   describing what to create. Unlike Midjourney, do NOT use compact comma-separated clauses.
   *Source: platform.openai.com/docs/guides/images*
2. **No negative prompt field:** The API does not support a separate negative prompt parameter.
   All "what to avoid" constraints must be embedded in the positive prompt as explicit
   prohibitions (e.g. "do not include text overlays", "avoid motion blur").
   `supports_negative_prompt: false` — `constraint_strategy: embedded_positive_constraints`.
   *Source: platform.openai.com/docs/guides/images*
3. **Iterative revision via conversation:** ChatGPT Image supports natural language revision
   of a previous generation. Subsequent prompts can reference "the previous image" to refine.
   `supports_natural_language_revision: true`.
   *Source: openai.com release announcement*
4. **Image editing support:** Can accept a reference image and edit/extend it.
   `supports_image_editing: true`.
   *Source: platform.openai.com/docs/guides/images*
5. **No seed parameter:** No native seed/reproducibility parameter in the public API.
   `supports_seed: false`.
   *Source: platform.openai.com/docs/guides/images*
6. **Detailed scene description:** Include: subject, action, environment, lighting,
   mood, style references, and explicit constraint text in one coherent paragraph.
   *Source: inferred from API docs + official examples*
7. **Style specification:** Reference established visual styles by name (e.g. "cinematic",
   "documentary photography"). Avoid trademarked style names per OpenAI usage policy.
   *Source: openai.com/policies/usage-policies — verify current policy*
8. **Constraint embedding pattern:** Instead of `--no <term>`, write:
   "Do not include [term]. Avoid [term]. [Term] must not appear."
   *Source: inferred from capability gap — no --no flag exists*

---

## Do Not Invent / Requires Verification

- Any parameter syntax (ChatGPT Image is prompt-only; no `--` flags)
- Exact constraint embedding wording (what phrasing OpenAI recommends)
- Current model version name (GPT-4o? image-1? — verify API model ID)

---

## Model Version Observed

- **Version string:** GPT-4o image generation *(verify current API model name)*
- **Confidence:** low *(placeholder)*

---

## Operator Action Required

Before the ChatGPT Image adapter runs in Batch 4:

1. Visit each source URL above.
2. Fill in `Retrieved at` and `HTTP status`.
3. Confirm `supports_negative_prompt: false` against current API docs.
4. Run: `python scripts/agents/run_pipeline.py --mode refresh-model-guidance --models chatgpt-image --save-snapshot`
5. Update `docs/model_guides/chatgpt_image.yaml` confidence level.
