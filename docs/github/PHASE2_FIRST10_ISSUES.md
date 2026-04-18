# Phase 2 — First 10 Issues

Open these issues using the `.github/ISSUE_TEMPLATE/` forms after pushing to GitHub.
Use the issue form chooser ("New issue") and select the matching template.

---

## Issue 1 — Epic

**Title:** `[P2][Epic] Phase 2 Visual Development Master Epic`
**Template:** 07-general-visual-task
**Labels:** `phase-2`, `task`
**Milestone:** P2-Batch-01 Reference Packs

**Objective:**
Master tracking issue for all Phase 2 Visual Development work. All character pack, location sheet, still set, motion pair, evidence panel, and freeze issues link back here.

**Inputs:** All planning records, style bible, continuity bible.

**Expected outputs:** Approved reference library, curated still sets, motion-ready frame pairs, evidence panels, visual-z1p2-batch1-r1 freeze.

**Review criteria:** All Batch 01 milestones complete, manifests updated, freeze issued.

---

## Issue 2 — Character Pack: Nadia

**Title:** `[P2][Character Pack] Create Nadia reference pack (C01)`
**Template:** 01-character-pack
**Labels:** `phase-2`, `asset-character`, `review-needed`, `article3-evidence`
**Milestone:** P2-Batch-01 Reference Packs
**Priority:** P0 | **Batch:** Batch 01 | **Character ID:** C01 | **Article 3:** Candidate

**Canonical inputs:**
- `planning/characters/C01.yaml`
- `planning/wardrobe/WD001.yaml`
- `source/style_bible.md`

**Required outputs:** front portrait, left profile, right profile, three-quarter, low-light variation, daylight variation, contact sheet, notes file.

**Output paths:** `visual_dev/characters/C01/`

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 3 — Character Pack: Roman

**Title:** `[P2][Character Pack] Create Roman reference pack (C02)`
**Template:** 01-character-pack
**Labels:** `phase-2`, `asset-character`, `review-needed`, `article3-evidence`
**Milestone:** P2-Batch-01 Reference Packs
**Priority:** P0 | **Batch:** Batch 01 | **Character ID:** C02 | **Article 3:** Candidate

**Canonical inputs:**
- `planning/characters/C02.yaml`
- `source/style_bible.md`

**Required outputs:** front portrait, left profile, right profile, three-quarter, low-light variation, daylight variation, contact sheet, notes file.

**Output paths:** `visual_dev/characters/C02/`

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 4 — Location Sheet: Vale Residence

**Title:** `[P2][Location Sheet] Create Vale residence reference sheet (LOC001)`
**Template:** 02-location-sheet
**Labels:** `phase-2`, `asset-location`, `continuity-risk`, `review-needed`, `article3-evidence`
**Milestone:** P2-Batch-01 Reference Packs
**Priority:** P0 | **Batch:** Batch 01 | **Location ID:** LOC001 | **Continuity Risk:** High | **Article 3:** Candidate

**Canonical inputs:**
- `planning/locations/LOC001.yaml`
- `source/style_bible.md`
- `planning/props/PROP001.yaml`

**Required outputs:** frontal, angled-left, angled-right, reverse-wide, 3 detail close-ups, contact sheet, notes file.

**Output paths:** `visual_dev/locations/LOC001/`

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 5 — Location Sheet: Nadia Study

**Title:** `[P2][Location Sheet] Create Nadia study reference sheet (LOC002)`
**Template:** 02-location-sheet
**Labels:** `phase-2`, `asset-location`, `review-needed`, `article3-evidence`
**Milestone:** P2-Batch-01 Reference Packs
**Priority:** P1 | **Batch:** Batch 01 | **Location ID:** LOC002 | **Article 3:** Candidate

**Canonical inputs:**
- `planning/locations/LOC002.yaml`
- `source/style_bible.md`

**Output paths:** `visual_dev/locations/LOC002/`

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 6 — Still Set: SC0001

**Title:** `[P2][Still Set] Generate SC0001 still set`
**Template:** 03-still-set
**Labels:** `phase-2`, `asset-still`, `article3-evidence`, `continuity-risk`, `review-needed`
**Milestone:** P2-Batch-01 Scene Stills
**Priority:** P0 | **Batch:** Batch 01 | **Scene ID:** SC0001 | **Continuity Risk:** High | **Article 3:** Approved

**Canonical inputs:**
- `planning/scenes/SC0001/scene_card.yaml`
- `planning/scenes/SC0001/scene_excerpt.md`
- `planning/scenes/SC0001/prompt_brief.md`
- `visual_dev/characters/C01/approved/`
- `visual_dev/locations/LOC001/approved/`

**Required outputs:** 1 establishing still, 2 character-centered stills, 1 detail/prop still, 1 tonal alternative, contact sheet, selection log.

**Output paths:** `visual_dev/stills/SC0001/`

**Dependencies:** Approved C01 reference pack; approved LOC001 reference sheet.

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 7 — Still Set: SC0006

**Title:** `[P2][Still Set] Generate SC0006 still set`
**Template:** 03-still-set
**Labels:** `phase-2`, `asset-still`, `article3-evidence`, `continuity-risk`, `review-needed`
**Milestone:** P2-Batch-01 Scene Stills
**Priority:** P0 | **Batch:** Batch 01 | **Scene ID:** SC0006 | **Continuity Risk:** High | **Article 3:** Approved

**Canonical inputs:**
- `planning/scenes/SC0006/scene_card.yaml`
- `planning/scenes/SC0006/scene_excerpt.md`
- `planning/scenes/SC0006/prompt_brief.md`
- `visual_dev/characters/C01/approved/`
- `visual_dev/locations/LOC002/approved/`

**Output paths:** `visual_dev/stills/SC0006/`

**Dependencies:** Approved C01 reference pack; approved LOC002 reference sheet.

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 8 — Motion Prep: SC0001

**Title:** `[P2][Motion Prep] Prepare SC0001 motion-ready frame pairs`
**Template:** 04-motion-pair
**Labels:** `phase-2`, `phase-2-motion-prep`, `asset-motion-pair`, `article3-evidence`, `review-needed`
**Milestone:** P2-Batch-01 Motion Prep
**Priority:** P1 | **Batch:** Batch 01 | **Scene ID:** SC0001 | **Motion Ready:** Paired | **Article 3:** Candidate

**Shot purpose:** Domestic surveillance establishing tension pair.

**Canonical inputs:**
- Approved stills from `visual_dev/stills/SC0001/approved/`
- `planning/scenes/SC0001/scene_card.yaml`
- `planning/scenes/SC0001/prompt_brief.md`

**Output paths:** `visual_dev/motion_prep/SC0001/`

**Dependencies:** Approved SC0001 still set.

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 9 — Motion Prep: SC0006

**Title:** `[P2][Motion Prep] Prepare SC0006 motion-ready frame pairs`
**Template:** 04-motion-pair
**Labels:** `phase-2`, `phase-2-motion-prep`, `asset-motion-pair`, `article3-evidence`, `continuity-risk`, `review-needed`
**Milestone:** P2-Batch-01 Motion Prep
**Priority:** P0 | **Batch:** Batch 01 | **Scene ID:** SC0006 | **Motion Ready:** Paired | **Article 3:** Approved

**Shot purpose:** Surveillance reveal close-up transition.

**Output paths:** `visual_dev/motion_prep/SC0006/`

**Dependencies:** Approved SC0006 still set.

**Freeze target:** `visual-z1p2-batch1-r1`

---

## Issue 10 — Evidence Panel

**Title:** `[P2][Evidence Panel] Prepare Batch 01 Article 3 panel set`
**Template:** 05-evidence-panel
**Labels:** `phase-2`, `asset-evidence`, `article3-evidence`, `review-needed`
**Milestone:** P2-Batch-01 Motion Prep
**Priority:** P0 | **Batch:** Batch 01 | **Article 3:** Approved

**Panel types to produce:**
- `prompt-to-still` (SC0001, SC0006)
- `still-to-motion` (SC0001, SC0006)
- `continuity comparison` (C01 across scenes)

**Source assets:** approved stills, approved motion pairs, selected prompts, scene excerpts, selection logs.

**Output paths:** `evidence/panels/`, `evidence/article3/`, `evidence/selection_logs/`

**Dependencies:** Approved SC0001 and SC0006 still sets and motion pairs.

**Freeze target:** `visual-z1p2-batch1-r1`
