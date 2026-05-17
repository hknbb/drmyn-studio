# PR-GOLDEN-0 — Golden Scene Candidate Analysis & Selection

**Phase:** 8 (Golden Scene Selection)
**Status:** Selected
**Decision:** **SC0001 — Vale Residence Morning Inventory** is selected as the golden reference scene for full end-to-end Kling Omni 3 production (Phase 9 / PR-GOLDEN-1..7).
**Plan reference:** `revised_character_batch_to_golden_scene_plan.md` § Phase 8.
**Date:** 2026-05-17.

---

## 1. Selection Criteria

```text
Nadia central?
Herald / Halo Unit pressure?
Roman / Dimitri / Zara / Jin / Sera required?
Dialogue?
Camera movement and shot coverage potential?
Insert / detail / reaction / final hold coverage?
Element readiness complete (post Phases 2–7)?
```

Each criterion scored 0–3 (0 = absent, 1 = weak, 2 = moderate, 3 = strong) in §3.

---

## 2. Element Readiness Snapshot (main branch, 2026-05-17)

```text
C01 Nadia v2          ✓ KLING_REF_C01_NADIA_CANON_V2_V001 (look_variants path)
C02 Roman v2          ✓ KLING_REF_C02_V001
C03 Birta v2          ✓ KLING_REF_C03_V001
C04 Dimitri v2        ✓ KLING_REF_C04_V001
C05 Marcus v2         ✓ KLING_REF_C05_V001
C06 Zara v2           ✓ KLING_REF_C06_V001
C07 Sera v2           ✓ KLING_REF_C07_V001
C08 Jin v2            ✓ PR-JIN-1 scaffold merged; PR-JIN-2 visual production PR #231 still OPEN
HERALD_HALO           ✓ KLING_REF_HERALD_HALO_V001
LOC001 Vale Residence v1 grandfathered (no v2; per plan invariant, grandfathered OK for production)
PROP003 Vardova frame v1 grandfathered (same)
Other LOC / PROP      v1 only or undefined
```

PR #231 (C08 Jin visual production) does not block SC0001 because SC0001 does not require C08 in foreground. Jin is referenced (Nadia checks on him in the crib) but not framed as a visible production element in SC0001's 8 omni clips.

---

## 3. Candidate Scoring Matrix

Categories from `revised_character_batch_to_golden_scene_plan.md` § Phase 8. Score range 0–3 per criterion. **Higher = stronger.** "Readiness" is the deciding tiebreaker because Phase 9 is full end-to-end production (not concept exploration).

```text
Scene  Category                                Nadia  Herald  Other-char  Dialogue  Coverage  Readiness  Total
=====  ======================================  =====  ======  ==========  ========  ========  =========  =====
SC0001  A Vale Residence domestic opening       3      0       2 (C03)      3         3         3          14
SC0018  B Herald first contact (warehouse)      3      3       0            1         1         1          9
SC0079  C/D Zara alliance turning point         3      0       3 (C06)      3         1         2          12
SC0099  D Zara north-gate sacrifice             1      0       3 (C06+NPC)  2         1         2          9
SC0101  E Sera publication / evidence leak      1      0       3 (C07,C02)  1         2         2          9
SC0109  C ORACLE PRIME shutdown (Veltain)       3      2       2 (C02)      0         2         2          11
SC0110  C Roman confrontation (corridor combat) 3      0       3 (C02)      0         2         2          10
```

**Scoring notes:**

- **Coverage** rewards scenes with an existing `omni_clip_plan.yaml` (shot breakdown drafted) — only SC0001 has this.
- **Readiness** rewards scenes whose required characters AND location have v2 production records. SC0001 wins because LOC001 is grandfathered v1 (operationally usable) and only C01+C03 are needed.
- Scenes with C06 / C07 / HERALD_HALO have only character v2 but no scene-level shot manifests, dialogue beats, or location v2 — they would require significant net-new scaffolding before Phase 9 can execute.

---

## 4. Per-Scene Detail

### A) SC0001 — Vale Residence Morning Inventory **[SELECTED]**

- **Files:** `scene_card.yaml`, `scene_excerpt.md`, `dialogue_beats.yaml`, `omni_clip_plan.yaml`, `scene_beat_plan.yaml`, `prompt_brief.md`, `review_notes.md`, `manifests/CLIP_SC0001_01-08_manifest.yaml`, `visual_dev/omni_sets/SC0001/element_set.yaml`, `element_bindings.yaml`, `scene_character_look_map.yaml`, `shot_element_manifests/SH001.yaml`, `video_takes.yaml`, `selected_take.yaml`
- **Synopsis:** Nadia performs a precise morning domestic routine in her expensive, underused home. Inventory routine reads as a threat-map. Brief exchange with Birta about Jin's care and Roman's early departure. Discovers a family photo frame has been moved — the surveillance intrusion cue. Checks on Jin. Establishes Nadia's contained, hypervigilant baseline.
- **Required elements:** C01 (Nadia, v2), C03 (Birta, v2), LOC001 (v1 grandfathered), PROP003 (v1 grandfathered). C08 (Jin) appears off-camera in crib — does not require visible character production.
- **Dialogue:** 8 lines / 5 beats / 2 speakers (Nadia, Birta). `native_audio_readiness: blocked` per current state — golden scene Phase 9 will render dialogue only after `native_audio_readiness == ready` (per plan invariant).
- **Coverage:** 8 omni clips already drafted (~97s total) covering establishing, character coverage, dialogue, reaction, insert/detail (photo frame), movement, final hold.
- **Narrative weight:** Opening calibration + inciting incident (surveillance intrusion revealed through object deviation).
- **Production readiness:** All required v2 characters present. Locations and props grandfathered. 7 of 8 shot element manifests need to be created (SH001 exists; SH002–SH08 require new files). Dialogue rendering blocked until native_audio_readiness; visual-only shot plan can proceed.

### B) SC0018 — Herald First Contact

- **Files:** `scene_card.yaml`, `scene_excerpt.md`, `prompt_brief.md`, `review_notes.md`
- **Synopsis:** Nadia encounters a HALO UNIT in a warehouse passage. The Herald's voice emanates from it, delivering odds, competition intel, and framing the event as broadcast performance. Nadia absorbs silently and walks past.
- **Required elements:** C01 (Nadia, v2), HERALD_HALO (v2), warehouse-passage location (undefined). HALO UNIT visual element is v2 ready.
- **Dialogue:** Heavy Herald exposition; minimal Nadia.
- **Coverage:** No `omni_clip_plan` exists yet; would require full shot breakdown from scratch.
- **Narrative weight:** Inciting incident for the broadcast architecture; introduces Herald as game operator. Symbolically strong but production-asset-light.
- **Readiness gap:** New location intake required; voice-audio architecture for Herald not yet defined; dialogue beats not extracted; no omni clips.

### C) SC0079 — Zara Alliance Turning Point

- **Files:** `scene_card.yaml`, `scene_excerpt.md`, `prompt_brief.md`, `review_notes.md`
- **Synopsis:** Nadia and Zara meet in a grid-blind corridor at Kaspar Terminal. Explicit two-way negotiation: Nadia trades intelligence dismantling Zara's debt for VELTAIN access credentials. Agreement made with mutual recognition, no warmth.
- **Required elements:** C01 (Nadia, v2), C06 (Zara, v2), Kaspar Terminal storage corridor location (undefined).
- **Dialogue:** 136-line dense negotiation. Dialogue beats not yet extracted.
- **Coverage:** No `omni_clip_plan` exists yet.
- **Narrative weight:** Phase 7 SP03 turning point; sets up VELTAIN entry sequence.
- **Readiness gap:** New location intake; dialogue beats extraction; omni clip plan from scratch; native_audio_readiness path required for the negotiation.

### C / climax) SC0109 — ORACLE PRIME Shutdown

- **Files:** `scene_card.yaml`, `scene_excerpt.md`, `prompt_brief.md`, `review_notes.md`
- **Synopsis:** Nadia inserts Morrow's credential into a non-networked reader. ORACLE PRIME shuts down in ~43s. Roman exits an adjacent room as silence falls.
- **Required elements:** C01 (Nadia, v2), C02 (Roman, v2), Veltain server-core antechamber location (undefined). ORACLE PRIME broadcast architecture has no character record.
- **Dialogue:** None (system readouts only).
- **Coverage:** No `omni_clip_plan` yet.
- **Narrative weight:** Climax turning point.
- **Readiness gap:** Location + ORACLE PRIME visual identity work; precise machine-shutdown SFX/sound-design dependency; choreography for Roman's entrance.

### D) SC0099 — Zara North-Gate Sacrifice

- Strong character beat for Zara but C01 is off-stage; requires C06 v2 (✓) + Hilda Krast NPC v2 (no record) + Veltain perimeter location (undefined). Net-new scaffolding for an NPC and a location. Score lower than SC0079 because Nadia is not central.

### E) SC0101 — Sera Publication / Evidence Leak

- Multi-location parallel sequence (Keston / Veltain control room / Sera workspace). Requires C07 (Sera, v2 ✓) + C02 (Roman, v2 ✓) + Keston Lale NPC + 3 separate locations (none v2). High narrative value but heavy net-new infrastructure burden.

---

## 5. Decision

**Selected scene:** **SC0001 — Vale Residence Morning Inventory.**

**Primary rationale:**

1. **Highest existing-infrastructure ratio.** 8 omni clips already drafted, 5 dialogue beats specified, `shot_element_manifests/SH001.yaml` exists, `element_set.yaml` and `element_bindings.yaml` exist, `scene_character_look_map.yaml` exists, `selected_take.yaml` recorded. No other candidate has this completeness.

2. **All required production elements available on main.** C01 Nadia v2 and C03 Birta v2 are merged. LOC001 and PROP003 are v1 grandfathered (per plan invariants, this is operationally usable for golden production — promotion to v2 is a separate later concern).

3. **Strong narrative anchor without over-scope.** Opening calibration scene + inciting incident (surveillance intrusion through PROP003 photo frame) gives the golden reference real dramatic weight without climax-scale choreography/SFX/multi-location complexity.

4. **Dialogue can be deferred without blocking visual production.** Plan invariant says dialogue is rendered only when `native_audio_readiness == ready`. SC0001 dialogue is `blocked`. The 8-shot visual coverage (establishing → entrance → dialogue cover-frame-only → reaction → insert/detail → movement → final hold) can produce as a silent-cover golden reference; native audio is a follow-up promotion.

5. **C08 Jin (PR #231 still open) is not a blocker.** SC0001 places Jin off-screen in the crib; the scene does not require a visible Jin production element in any of the 8 clips.

**Out of scope for this selection (explicitly):**

- HERALD_HALO scenes (SC0018+) — symbolically attractive but production-asset light; would require full scaffolding (location, voice-audio architecture, dialogue beats, clip plan)
- Climax scenes (SC0109, SC0110) — would require Veltain location intake, choreography pipeline, and SFX/sound-design dependencies not yet established
- Zara turning-point (SC0079) and Sera publication (SC0101) — both require net-new location records and dialogue beats extraction

---

## 6. Hand-off to Phase 9 (PR-GOLDEN-1..7)

PR-GOLDEN-1: produce `planning/scenes/SC0001/golden_reference_plan.yaml` + register the new `golden_reference_plan` record type in the validator + add JSON schema.

PR-GOLDEN-2: add 7 new shot element manifests at `visual_dev/omni_sets/SC0001/shot_element_manifests/SH002.yaml`–`SH008.yaml`. SH001 already exists.

PR-GOLDEN-3: add alias-only Kling Omni prompt records under `visual_dev/motion_prep/SC0001/`. `prompt_text` uses ONLY registered `@aliases` (`@Nadia` v1 already bound; defer @Nadia → C01_NADIA_CANON_V2 alias migration; `@Birta` already bound). Dialogue suppressed until `native_audio_readiness == ready`.

PR-GOLDEN-4: register `video_take` metadata per shot per take after external Kling generation. No binary commits.

PR-GOLDEN-5: per-take QC via `video_review` records (existing pattern in `evidence/video_reviews/`).

PR-GOLDEN-6: update `selected_take.yaml` per shot.

PR-GOLDEN-7: assembly metadata (`evidence/scene_clip_map.csv` append, `planning/scenes/SC0001/golden_scene_assembly.yaml`, `evidence/operator_sessions/OP-GOLDEN-SC0001-*.yaml`).

Final tag: `v0.18.0-golden-reference-scene` after PR-GOLDEN-7 merges and `python scripts/agents/scene_readiness.py --scene SC0001` reports READY for all SH001–SH008.

---

## 7. Open follow-ups (do NOT block PR-GOLDEN-0)

- @Nadia alias migration to C01_NADIA_CANON_V2 — separate later PR per the C01-v2 isolation discipline
- LOC001 / PROP003 v2 promotion — separate optional improvement (not required for golden scene production per plan invariants)
- C08 Jin visual production (PR #231) — merges independently; does not affect SC0001 production path

---

## 8. Validation guarantee

This PR is docs-only and adds no production records, schemas, or validator changes. Validation expectations:

```bash
python scripts/validate_production_records.py --repo-root .   # → 144 / 144 valid (unchanged)
python -m pytest -q                                            # → 1441 passed (unchanged)
python scripts/check_referential_integrity.py …               # → 0 errors (unchanged)
```
