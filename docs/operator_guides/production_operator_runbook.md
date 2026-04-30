# Production Operator Runbook
## NexusZeroClosingPriceProduction — Closing Price Film

**Skeleton introduced: Batch 0.5**
**Full content: Batch 5.85 (Operator Guidance Layer)**

This runbook tells the human operator exactly what to do at each production stage:
which file to open, which prompt to paste into which external tool, where to save
outputs, and which CLI command to run next.

---

## Quick Reference — Production Phases

| Phase | Goal | Status |
|---|---|---|
| **Phase 1** | T2I Element Prompts (characters, locations, props, style) | Batch 1–5.5 |
| **Phase 2** | Scene Still + Storyboard Options | Batch 5.75 |
| **Phase 3** | Kling Omni Video Generation | Batch 8 |

---

## Before Any Prompt Generation — Required Pre-Flight

### Step 1: Verify Model Guidance Snapshots

```bash
# Run before every batch of prompt generation
python scripts/agents/run_pipeline.py \
  --mode refresh-model-guidance \
  --models midjourney,chatgpt-image,nano-banana \
  --save-snapshot
```

Check: `evidence/model_guidance_snapshots/` — confirm one file per model, created today.

### Step 2: Verify Guide Files Are Active

Check `docs/model_guides/midjourney.yaml`, `chatgpt_image.yaml`, `nano_banana.yaml`:
- `status:` must be `active` (not `draft` or `stub`)
- At least one `source_refs` entry must have `human_verified: true`

If any guide is `draft`:
1. Open `docs/model_guides/sources/{model}_research_log.md`
2. Visit each source URL
3. Set `human_verified: true` for verified rules
4. Change `status: draft` → `status: active`
5. Commit the update

---

## Phase 1 — T2I Element Prompt Generation

*(Full playbook: `docs/operator_guides/t2i_image_generation_playbook.md` — Batch 5.85)*

### Overview

1. Agent generates prompt YAMLs in `prompts/draft/`
2. Operator copies prompt text into external generation tool
3. Operator saves candidate images locally
4. Agent reviews candidates → writes `image_selection.yaml`
5. Human PR promotes `pack_status` to `seeded` → `approved` → `locked`

### Key Commands

```bash
# Generate T2I prompts for a scene
python scripts/agents/run_pipeline.py \
  --mode generate-prompts \
  --scene-id SC0001 \
  --models midjourney,chatgpt-image,nano-banana \
  --model-guidance-snapshot-dir evidence/model_guidance_snapshots/

# After generating and saving candidates:
python scripts/agents/run_pipeline.py \
  --mode review-outputs \
  --prompt-id SC0001__t2i-char-nadia-midjourney__v01 \
  --images visual_dev/elements/characters/C01/candidates/ \
  --review-notes evidence/prompt_reviews/SC0001__t2i-char-nadia-midjourney__v01_review.md
```

---

## Phase 2 — Storyboard Options

*(Full playbook: `docs/operator_guides/storyboard_selection_playbook.md` — Batch 5.85)*

### Overview

1. Agent generates ≥5 composition options per scene
2. Operator selects one composition
3. Agent generates scene still prompts for selected composition
4. Human PR records selection

### Key Command

```bash
python scripts/agents/run_pipeline.py \
  --mode generate-storyboard-options \
  --scene-id SC0001
```

---

## Phase 3 — Kling Omni Video Generation

*(Full playbook: `docs/operator_guides/kling_omni_generation_playbook.md` — Batch 5.85)*

**BLOCKED UNTIL:**
- All element packs `pack_status: locked`
- Storyboard direction selected
- `shot_list_omni` non-empty in scene_card.yaml
- `docs/model_guides/kling_omni.yaml` is `status: active`
- Fresh Kling snapshot (< 7 days)

---

## Review & Approval Process

*(Full guide: `docs/operator_guides/review_and_approval_playbook.md` — Batch 5.85)*

Human-gated lifecycle gates:
- Prompt records: `draft` → `approved` via PR
- Element packs: `metadata_only` → `seeded` → `approved` → `locked` via PR
- Agent writes `pack_manifest_update_suggestion.yaml` — human applies to `pack_manifest.yaml`
- Agents NEVER update `pack_status`, `canon_lock`, `approved`, or `locked` fields directly

---

## Storage Policy Quick Reference

| Asset type | Where it lives |
|---|---|
| Prompt YAMLs | `prompts/draft/` (agent writes) |
| Element images (canonical) | `visual_dev/elements/{type}/{id}/` + Git LFS |
| Element candidates (≤20/element) | `visual_dev/elements/{type}/{id}/candidates/` + Git LFS |
| Storyboard locked keyframes | `visual_dev/storyboards/SC####/frames/` + Git LFS |
| Kling video takes | External storage only (never commit .mp4/.mov) |
| Post proxies | External storage only |
| Evidence / metadata YAMLs | `evidence/` (plain git, no LFS) |

Full policy: `docs/methodology/storage_policy.md`

---

## Getting Help

- Full architecture: `docs/methodology/agent_prompt_pipeline.md` (Batch 6)
- Pipeline status: `evidence/production_status.csv` (Batch 5.8)
- Next step helper: `python scripts/agents/operator_next_step.py` (Batch 5.85)

---

*Skeleton introduced: Batch 0.5. Full content added: Batch 5.85.*
