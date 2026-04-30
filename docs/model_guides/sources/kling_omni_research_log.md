# Kling Omni Prompt Guidance — Research Log

**Batch:** 0.25
**Purpose:** Human-curated source log for the Kling Omni model guide.
This file records which official sources were consulted, what was found,
and what rules were extracted. It is the evidence base for `docs/model_guides/kling_omni.yaml`.

**Status:** Seed skeleton. Kling Omni is Phase 3 only.
**Do not run Kling Omni adapter until:**
1. All required element packs are `pack_status: locked`
2. Storyboard visual direction selected for the scene
3. `shot_list_omni` field in scene_card.yaml is non-empty (populated via Batch 7.5)

**Freshness policy:** `max_age_days: 7` (faster release cadence than image models).
The Kling Omni snapshot must be refreshed at least every 7 days before prompt generation.

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

### Source 1 — Kling Platform Documentation
- **URL:** https://klingai.kuaishou.com/docs *(verify current URL)*
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Main Kling Omni prompt and generation reference.

### Source 2 — Kling Omni Feature Announcement
- **URL:** *(operator finds official Kling Omni release post)*
- **Source class:** `official_release_notes`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Kling Omni specifically adds elements/character consistency to video generation.

### Source 3 — Kling API / Developer Docs
- **URL:** *(operator finds Kling API docs if available)*
- **Source class:** `official_docs`
- **Retrieved at:** *(operator fills in)*
- **HTTP status:** *(operator fills in)*
- **Human verified:** false
- **Notes:** Camera motion parameters, duration limits, element reference format.

---

## Extracted Prompt Rules (Draft)

> ⚠️ Seed rules only. Operator must verify before `confidence: high`.
> Kling updates frequently — verify within 7 days of any batch run.

1. **Video generation scope:** Kling Omni generates short video clips, not images.
   `output_type: video`, `max_duration_seconds: 10`.
   *Confidence: medium — verify current max duration*
2. **Elements support:** Kling Omni accepts element references (character images, location images)
   to maintain visual consistency across video frames.
   `supports_elements: true`.
   *Confidence: medium — verify element upload format*
3. **Camera motion support:** Kling Omni supports explicit camera movement instructions
   (pan, tilt, zoom, track, static, etc.).
   `supports_camera_motion: true`.
   *Confidence: medium — verify parameter format*
4. **No negative prompt field:** Kling Omni uses a different instruction format.
   `supports_negative_prompt: false`.
   *Confidence: low — verify in current API docs*
5. **Multimodal instruction format:** Prompts should describe:
   - Subject action + physical state
   - Camera movement instruction
   - Environment/lighting
   - Duration intent
   *Confidence: medium — verify against official generation guide*
6. **Shot_list_omni integration:** The `shot_list_omni` field in scene_card.yaml
   defines shot type, camera movement, subject, and duration per shot.
   The Kling Omni adapter reads this field and must refuse to generate if empty.
   *Source: plan constraint — not a Kling API rule*
7. **Blocking conditions:** Adapter is blocked if:
   - `shot_list_omni` is empty (all pilot scene cards have `shot_list_omni: []`)
   - Required element pack is not `pack_status: locked`
   - No selected storyboard option for the scene
   *Source: plan Phase 3 gate conditions*

---

## Do Not Invent / Requires Verification

- Exact camera motion parameter names and values
- Element reference image format (URL? base64? file attachment?)
- Current maximum clip duration (confirmed: 10s? or longer?)
- Whether seed/reproducibility is supported
- Current API authentication method

---

## Model Version Observed

- **Version string:** *(operator fills in — e.g. "Kling Omni 1.6")*
- **Confidence:** low *(placeholder)*

---

## Phase 3 Prerequisites Checklist

Before any Kling Omni prompt is generated, verify all of these:

- [ ] `docs/model_guides/kling_omni.yaml` has `confidence: high` (after operator verification)
- [ ] Snapshot is fresh (< 7 days old)
- [ ] All element packs for the scene are `pack_status: locked`
- [ ] Storyboard option selected (`selected_option` non-null in `storyboard_options.yaml`)
- [ ] `shot_list_omni` is non-empty in scene_card.yaml (applied via Batch 7.5 PR)
- [ ] `visual_dev/storyboards/SC####/shot_list_omni_suggestion.yaml` has `applied_to_scene_card: true`

---

## Operator Action Required

Before the Kling Omni adapter runs in Batch 8 (Phase 3):

1. Find and visit official Kling Omni documentation.
2. Fill in source URLs, `Retrieved at`, `HTTP status`.
3. Verify all capability matrix flags.
4. Note exact camera motion parameter format.
5. Run: `python scripts/agents/run_pipeline.py --mode refresh-model-guidance --models kling-omni --save-snapshot`
   (Do this within 7 days of planned video generation batch.)
6. Update `docs/model_guides/kling_omni.yaml`.
7. Ensure all Phase 3 prerequisite conditions above are met before proceeding.
