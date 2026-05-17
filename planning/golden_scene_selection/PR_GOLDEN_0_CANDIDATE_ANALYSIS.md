# PR-GOLDEN-0 — Golden Scene Candidate Analysis & Selection

**Phase:** 8 (Golden Scene Selection)
**Status:** Amended twice — selection returned to original choice
**Current decision (AUTHORITATIVE):** **SC0001 — Vale Residence Morning Inventory** is the golden reference scene for full end-to-end Kling Omni 3 production (Phase 9 / PR-GOLDEN-1..7). See **§ 10. Revision 2 — 2026-05-18** below for the revert record.
**Selection history:**
- 2026-05-17: SC0001 selected (original analysis, §§ 1–8)
- 2026-05-18 (earlier): SC0089 selected (Revision 1, § 9 — now superseded)
- 2026-05-18 (later): SC0001 reselected (Revision 2, § 10 — current)
**Plan reference:** `revised_character_batch_to_golden_scene_plan.md` § Phase 8.
**Original analysis date:** 2026-05-17.
**Most recent amendment date:** 2026-05-18 (Revision 2).

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

### A) SC0001 — Vale Residence Morning Inventory **[CURRENT SELECTION — reselected 2026-05-18, see § 10]**

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

---

## 9. Revision 1 — 2026-05-18 — Selection changed from SC0001 to SC0089 [SUPERSEDED by § 10]

**Status of this section:** **SUPERSEDED by § 10 (Revision 2).** Preserved verbatim as audit trail of the brief SC0089 selection window. Do not apply any directives from this section; use § 10 instead.

### 9.1 Selection deltas

```text
previous_selection: SC0001
  status: previously_selected_superseded
  reason: lower system/action coverage compared with SC0089
  preserved_as: audit_trail (§§ 1–8 above unchanged)

new_selection: SC0089
  selection_type: golden_reference_scene
  status: selected
```

### 9.2 Revision reason

```text
- stronger action density
- multi-character roster relevance (C01 + C06 + C04 V.O.)
- better golden-scene stress test (kinetic infiltration + sound design)
- C01 + C06 visual readiness on main (KLING_REF_C01_NADIA_CANON_V2_V001, KLING_REF_C06_V001)
- C04 V.O. can remain non-visual / suppressed (radio voice only, no on-camera frame)
- wardrobe delta can be handled through prompt-level continuity (no new asset required)
- better camera/coverage potential before climax (7 natural shots vs SC0001's 8 dialogue-anchored clips)
- dialogue-suppression rule (native_audio_readiness != ready) does not break SC0089 because dialogue load is minimal (Dimitri radio V.O. + minimal exchange + breath/action)
```

### 9.3 SC0089 — Northern Transit Corridor (selected)

- **Files:** `planning/scenes/SC0089/scene_card.yaml`, `scene_excerpt.md`, `prompt_brief.md`, `review_notes.md`.
- **Phase:** SEQ18 / PH_CRUCIBLE (pre-climax peak action).
- **Synopsis:** Nadia and Zara move through a lit-pool outer-perimeter transit corridor under Dimitri's coordinated multi-vector hunt. They detect a second team via wall-vibration acoustics, scale the drainage embankment, take down an advance operative, Zara is hit by a suppressed round from an unanticipated third vector, they drag-walk fifty meters to the drainage cut and disappear into the maintenance conduit. Dimitri's radio closes the scene: "All elements converge."
- **Required elements (on-camera):** C01 Nadia v2 ✓, C06 Zara v2 ✓.
- **Required elements (off-camera):** C04 Dimitri V.O. only (no visual frame; radio voice only — visual production not required).
- **Required elements (silhouette/nameless):** advance hunter operative (single takedown shot, low-light silhouette, no identity establishment — handled via prompt-level "anonymous tactical operative" instruction, no character record needed).
- **Locations:** outer perimeter transit corridor (night, lit-pool intervals), drainage embankment, drainage cut conduit. No v2 location records currently; will use prompt-level scene construction grounded in scene_excerpt geometry — same grandfathered-location pattern PR-GOLDEN-0 originally accepted for LOC001.
- **Wardrobe:** **No new asset, no new look_variant.** Canonical KLING_REF_C01_NADIA_CANON_V2_V001 and KLING_REF_C06_V001 already encode field-operational continuity (dark fitted top, muted neutral palette for Nadia; hunter-pool tactical-adjacent layered top for Zara). Outdoor / night / cold-perimeter delta handled as prompt-level micro-continuity instruction only:
  ```text
  outer perimeter night layer over canonical dark fitted top;
  matte dark utility jacket; no decorative hardware;
  no redesign; preserve canonical identity and silhouette.
  ```
  If Kling generation fails to hold the jacket continuity or QC reports "wardrobe delta too large", a lightweight look_variant scaffold will be opened as a separate follow-up PR (not in PR-GOLDEN-1 scope).
- **Dialogue:** Minimal. Dimitri radio V.O. ("Northern corridor, confirm contact." / "Accelerate." / "Northern embankment. All elements converge.") + brief Nadia↔Zara whisper exchanges. `native_audio_readiness` still gates spoken-word rendering; SC0089 remains coherent under suppression because the dramatic motor is movement, sound design (suppressed round, vibration-through-seam, distant radio chatter), and breath — not spoken negotiation.
- **Coverage (7 shots, natural):**
  1. Corridor longshot establishing — lit-pool / dark interval rhythm
  2. Light-pool transit (two figures, controlled pace, low thermal signature read)
  3. Wall-vibration detection beat — Nadia's fingers on repair seam
  4. Embankment scale + takedown insert
  5. Zara wound reveal — hand returning dark from below jacket
  6. Drag-walk fifty meters to drainage cut
  7. Drainage cover pull + entry into conduit (cliffhanger close)
- **Narrative weight:** Pre-climax peak. Multi-vector Dimitri hunt confirms Roman's deployment escalation; first physical injury to an ally character; transactional Nadia↔Zara dynamic crosses into mutual-stakes territory; sets up VELTAIN infiltration sequence (SC0093 onward).
- **Production readiness:**
  - All required visible characters on main (C01 v2, C06 v2)
  - Dimitri (C04 v2) merged — only V.O. usage, no visual production
  - HERALD_HALO not required (this scene predates direct Halo presence in this corridor)
  - Locations grandfathered-equivalent (treated under same operational pattern as LOC001 in original §§ 5–6)
  - Wardrobe handled prompt-level (no asset PR)
  - Shot manifests: all 7 will be new files in PR-GOLDEN-2 (no SH001 exists for SC0089 yet)

### 9.4 Scoring matrix — SC0089 row added

```text
Scene  Category                                Nadia  Action  Other-char  Dialogue  Coverage  Readiness  Total
=====  ======================================  =====  ======  ==========  ========  ========  =========  =====
SC0089  Crucible pursuit (selected)             3      3       3 (C06+C04) 2*        3         3          17
SC0001  A Vale Residence (superseded)           3      0       2 (C03)     3         3         3          14
```

`*` Dialogue scored 2 (not 3) because suppressed-native-audio rendering does not damage the scene — minimal spoken load is a *strength* under the current gate, not a deficit. "Herald pressure" column from § 3 is reframed as "Action" for SC0089 because the dramatic register is kinetic, not broadcast-system pressure; the criteria spirit is "what is the scene stress-testing" and SC0089 stress-tests action choreography + sound design + multi-character coordination, where SC0001 stress-tested domestic continuity + insert/detail discipline.

### 9.5 Hand-off to PR-GOLDEN-1 (SC0089)

PR-GOLDEN-1 will produce:
```text
schemas/golden_reference_plan.schema.json                     [new]
scripts/validate_production_records.py                        [register golden_reference_plan record type]
planning/scenes/SC0089/golden_reference_plan.yaml             [new, populated for SC0089]
```

The SC0089 `golden_reference_plan.yaml` will encode the §9.3 contents in structured form, including the wardrobe `prompt_level_continuity_policy` directive verbatim.

### 9.6 What this amendment does NOT do

```text
- does NOT create golden_reference_plan.yaml (PR-GOLDEN-1)
- does NOT add the golden_reference_plan schema (PR-GOLDEN-1)
- does NOT modify the validator (PR-GOLDEN-1)
- does NOT open shot element manifests (PR-GOLDEN-2)
- does NOT generate Kling prompts (PR-GOLDEN-3)
- does NOT register video takes or QC reviews (PR-GOLDEN-4..5)
- does NOT touch C01 v2 or C06 visual records (no asset change)
- does NOT promote @Nadia alias, LOC001/PROP003 v2, or open any wardrobe look_variant
```

### 9.7 Validation guarantee (amendment)

Still docs-only. No production records, schemas, validator, or YAML data files touched.

```bash
python scripts/validate_production_records.py --repo-root .   # → unchanged record count, all valid
python -m pytest -q                                            # → unchanged pass count
python scripts/check_referential_integrity.py …               # → 0 errors (unchanged)
```

---

## 10. Revision 2 — 2026-05-18 — Selection returned from SC0089 to SC0001

**Status of this section:** **AUTHORITATIVE.** This revision supersedes both § 9 (Revision 1) and §§ 5–6 (original decision section's forward-looking framing). The original §§ 1–8 are re-applied for current planning under the deltas listed in § 10.3 below. § 9 is preserved as audit trail of the brief SC0089 selection window only.

### 10.1 Selection deltas

```text
current_selection: SC0001
  selection_type: golden_reference_scene
  status: selected
  reselected_from: SC0089 (Revision 1, § 9)
  alignment_with_original_decision: yes — restores §§ 5–6 selection rationale verbatim

previous_selection (Revision 1): SC0089
  status: superseded_returned
  reason_for_revert: repo readiness, dialogue/audio suppression infrastructure already proven on SC0001, lower production risk
  preserved_as: audit_trail (§ 9 above unchanged)

later_high_action_candidate: SC0089
  status: high_action_candidate_not_selected
  use: future golden-scene-2 or action-stress-test pilot once SC0001 golden pipeline lands
  preserved_as: § 9 entire body remains valid as candidate analysis if reactivated
```

### 10.2 Revert reason (operator-confirmed)

```text
- SC0001 already has strongest repo readiness on main
- C01 / C03 / LOC001 / PROP003 production pipeline records exist
- SC0001 already has a selected SH001 take registered (selected_take.yaml)
- dialogue suppression / native-audio infrastructure was proven on SC0001
- better pilot / golden-scene methodology demonstration target
- lower production risk before expanding to action-heavy SC0089
- C01 v2 (KLING_REF_C01_NADIA_CANON_V2_V001) merged on main this session;
  no further C01 v2 rebuild PR required before golden production
- SC0089 retained as later high-action candidate, not deprioritized as a future target
```

### 10.3 SC0001 — current selection (restored from §§ 5–6)

The original SC0001 selection rationale and per-scene detail in §§ 4.A and 5 are re-applied. The full content remains valid as written; the only structural change is **binding modernization** for the golden production:

```text
character bindings:
  C01  →  KLING_REF_C01_NADIA_CANON_V2_V001        (v2, this session)
  C03  →  KLING_REF_C03_V001                       (v2, already on main)
location bindings:
  LOC001  →  v1 grandfathered (unchanged)
prop bindings:
  PROP003  →  v1 grandfathered (unchanged)
off-camera / inferred:
  C08 (Jin)  →  no on-camera frame; off-screen crib presence only
```

**C01 v2 binding migration policy:** SH001 currently binds to the C01 v1 chain (HOME_MORNING look_variant era). The golden production will use C01 v2 (NADIA_CANON_V2). Migration handled in a small dedicated mini-PR **before** PR-GOLDEN-1 lands the `golden_reference_plan.yaml` — to keep the binding chain clean and avoid the golden plan record carrying a forward reference to an unmigrated alias. The mini-PR scope is binding fields only (no asset changes, no v1 record deletions — additive alias remap only).

**Wardrobe / look policy:** No new wardrobe asset and no new character look_variant required for SC0001. Canonical C01 v2 + C03 v2 references already encode the domestic-morning continuity. If Kling generation drifts from kitchen-passage staging or domestic palette during PR-GOLDEN-3, a lightweight micro-continuity prompt directive will be added at the shot-prompt level (same Seçenek A pattern as § 9.3 reserved for SC0089, but with domestic-morning anchors instead of outer-perimeter-night anchors).

### 10.4 Shot coverage for golden SC0001 (illustrative, finalized in PR-GOLDEN-2)

SH001 already exists as a selected-take shot manifest. The golden expansion will add additional coverage (SH002–SH007 candidates, exact count and intents finalized in PR-GOLDEN-2):

```text
SH001 (existing)   selected corridor / frame deviation coverage
SH002              Birta / Nadia dialogue entry coverage
SH003              formula / vitamin dialogue beat
SH004              tilted Vardova frame insert / detail
SH005              Nadia reaction close / threat-map hold
SH006              Birta exit / breakfast line coverage
SH007              final corridor hold / surveillance geometry close
```

The above is **illustrative coverage**, not a binding shot list. PR-GOLDEN-2 will produce the binding shot_element_manifests and may add, remove, or reorder shots based on alias readiness, dialogue suppression rule application, and SC0001's existing `omni_clip_plan.yaml` (which already references three Omni coverages: SC0001_OMNI01 establish_coverage, SC0001_OMNI02 action_or_deviation_coverage, SC0001_OMNI03 reaction_or_hold_coverage).

### 10.5 Scoring matrix — final position

```text
Scene  Category                                Nadia  Action/  Other-char  Dialogue  Coverage  Readiness  Total
                                                       Herald
=====  ======================================  =====  ======   ==========  ========  ========  =========  =====
SC0001  A Vale Residence (CURRENT SELECTION)    3      0        2 (C03)     3         3         3          14
SC0089  Crucible pursuit (high-action candidate) 3     3        3 (C06+C04) 2*        3         3          17
```

SC0089 still scores higher on the §9.4 weighted matrix, but the revert is driven by **production-readiness risk minimization** rather than scoring. The golden scene methodology lands first on the lower-risk SC0001 pilot; SC0089 (or another action-heavy candidate) can follow as a v0.18.x or v0.19.x golden-scene-2 once the SC0001 pipeline has shipped and the methodology is proven.

### 10.6 Revised execution order

```text
1. PR-GOLDEN-0 amendment Revision 2  (this PR)         — revert selection to SC0001
2. PR-C01-V2-BIND mini-PR             — migrate SC0001 SH001 + omni / element bindings to C01 v2 (alias remap, no asset changes)
3. PR-GOLDEN-1                        — golden_reference_plan schema + SC0001 record + validator registration
4. PR-GOLDEN-2                        — SC0001 full shot element manifests (SH002–SH007 new; SH001 kept)
5. PR-GOLDEN-3                        — SC0001 alias-only Kling Omni prompt records
6. PR-GOLDEN-4                        — Kling take metadata per shot per take
7. PR-GOLDEN-5                        — video_review QC per take
8. PR-GOLDEN-6                        — selected_take updates
9. PR-GOLDEN-7                        — scene_clip_map append + golden_scene_assembly + operator session
10. tag v0.18.0-golden-reference-scene
```

C01 clean v2 scaffold / visual registration steps from the user's recap are **already done on main** this session (KLING_REF_C01_NADIA_CANON_V2_V001 merged with operator-approved Stage 3 three-view pack). They do not need to be re-opened as PR-C01-1 / PR-C01-2. Only the binding migration (step 2 above) remains before PR-GOLDEN-1.

### 10.7 What this amendment does NOT do

```text
- does NOT touch any production record, schema, or validator
- does NOT migrate the C01 v2 binding (deferred to PR-C01-V2-BIND mini-PR)
- does NOT create golden_reference_plan.yaml (PR-GOLDEN-1)
- does NOT modify SH001 or any visual_dev/omni_sets/SC0001/ file
- does NOT delete or weaken § 9 (Revision 1 SC0089 analysis remains intact as future candidate analysis)
```

### 10.8 Validation guarantee (Revision 2)

Still docs-only. Only `planning/golden_scene_selection/PR_GOLDEN_0_CANDIDATE_ANALYSIS.md` modified.

```bash
python scripts/validate_production_records.py --repo-root .   # → unchanged record count, all valid
python -m pytest -q                                            # → unchanged pass count
python scripts/check_referential_integrity.py …               # → 0 errors (unchanged)
```
