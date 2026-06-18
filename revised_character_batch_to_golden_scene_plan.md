# Revised Production Plan — Character Batch PR → C01/Halo/Zara/Jin/Sera → Golden Scene

**Status:** Revised after v0.17.0 public methodology checkpoint and in-session character visual production.  
**Decision:** Character-only production records do **not** require a new Zenodo DOI/public release. The v0.17.0 DOI remains the public methodology checkpoint. New character visuals proceed through normal private production PRs and optional private checkpoint tags.

---

## 0. Current Production State

### Public Methodology Checkpoint

The public methodology checkpoint already exists:

```text
v0.17.0-public-methodology-checkpoint
Zenodo DOI: 10.5281/zenodo.20241807
```

This DOI represents the methodology/system checkpoint, not every later character production record.

### Produced Character Visuals So Far

The following key characters have been produced or are ready to be registered/finalized as a first visual batch:

```text
C02 — Roman Vale
C03 — Birta
C04 — Dimitri Koss
C05 — Marcus Chen
```

These should be closed in a **single focused batch PR** before starting new production work.

---

## 1. Decision: Batch PR Before New Work

### Yes — Do One Batch PR First

Before starting C01 clean rebuild, Halo Unit, Zara, Jin, Sera, or golden scene work, close the already-produced characters in one batch PR.

### PR-BATCH-KEYCHAR-1

```text
chore(characters): register key character v2 visual batch
```

### Scope

Only these characters:

```text
C02 Roman Vale
C03 Birta
C04 Dimitri Koss
C05 Marcus Chen
```

### Purpose

This PR converts the currently produced character visual work into complete repo metadata:

```text
reference_chain.yaml updates
gpt_images_perspective_pack.yaml updates
gptimg2_perspectives/image_selection.yaml
perspective QC records
local media index records
kling_element_reference.yaml records
kling_elements alias cleanup
status transitions where justified
```

### Why Batch First?

```text
1. These characters are already produced.
2. Their v2 scaffolds already exist.
3. Closing them together gives a clean private checkpoint.
4. It prevents C01/Halo/Zara/Jin/Sera work from mixing with unfinished earlier character records.
5. It makes later golden-scene readiness easier to inspect.
```

---

## 2. PR-BATCH-KEYCHAR-1 Detailed Scope

### Per Character Required Updates

For each of C02/C03/C04/C05:

```text
1. reference_chain.yaml
   - Stage 1 winner external ref registered
   - Stage 2 winner external ref registered, if used
   - handoff.source_reference_id points to the final selected source reference
   - status moves from draft to review only if real refs are complete

2. gpt_images_perspective_pack.yaml
   - source_reference_id points to final Stage 2 / handoff source
   - perspective_policy remains three_view_scale_angle_v2
   - all three prompts remain:
     front_reference
     three_quarter_medium_reference
     three_quarter_close_reference
   - no left/right/profile wording reintroduced

3. gptimg2_perspectives/image_selection.yaml
   - selected file refs for all three views
   - quality scores
   - external/local media refs only

4. evidence/perspective_qc/
   - PQC_<CID>_PERSPECTIVE_PACK_V001.yaml
   - all three views scored
   - all required views pass
   - can_advance_to_kling_reference: true if eligible

5. evidence/local_media_indices/
   - LOCAL_MEDIA_INDEX_<CID>_GPTIMG2_PERSPECTIVES_V001.yaml
   - no binary committed
   - local/external refs only

6. kling_element_reference.yaml
   - v2 perspective keys:
     front_reference
     three_quarter_medium_reference
     three_quarter_close_reference
   - references the selected GPT Images 2 views

7. kling_elements/KLING_ELEM_<CID>_*.yaml
   - perspective_pack_id no longer null
   - front_hero_lock_ref / source refs no longer stale pending refs if real refs exist
   - alias record points to the current v2 Kling reference
```

### Important C03 Note

C03 Birta may have already advanced visually, but any deferred `kling_elements` cleanup must be closed in this batch PR if possible.

### Do Not Include

```text
C01 clean rebuild
Halo Unit system-character schema
Zara intake
Jin intake
Sera intake
Golden scene selection
Native audio readiness promotion
Dialogue prompt generation
Video/Kling generation
Zenodo/public release changes
```

---

## 3. Batch PR Validation

Before opening PR:

```bash
python scripts/validate_production_records.py --repo-root .
python -m pytest -q
```

If touching SC0001 or element bindings:

```bash
python scripts/agents/scene_readiness.py --scene SC0001
```

Expected:

```text
production records: all valid
tests: all pass
no binary media committed
no lifecycle promotion without human approval
```

### Optional Private Checkpoint Tag

After PR-BATCH-KEYCHAR-1 merges:

```text
v0.17.1-key-character-visual-batch
```

This is optional and private. It does not require Zenodo DOI.

---

## 4. DOI / Zenodo Policy Going Forward

### No New DOI For Character-Only Work

Character visual production alone does not require a new Zenodo DOI.

Use normal private PRs for:

```text
character visual refs
reference chains
QC records
Kling element references
local media indices
element bindings
```

### New DOI Only When System or Public Artifact Changes

Consider a new public release / Zenodo DOI only for:

```text
new methodology/schema/validator change
public dataset/checkpoint intended for citation
full golden reference scene completed
new reproducible research artifact
```

### Next Likely DOI

```text
v0.18.0-golden-reference-scene
```

This should happen only after the golden scene is fully produced, QC’d, selected, assembled, and documented.

---

## 5. Phase 1 — Character Visual Priority Roadmap

After the batch PR, create the roadmap PR.

### PR-CHAR-0

```text
docs(characters): add visual priority roadmap for golden scene production
```

### Purpose

Document the character production order and prevent compact planning IDs from being confused with source-truth IDs.

### Roadmap

```text
C01 Nadia Vale
- planning/source: C01
- role: protagonist
- action: clean v2 rebuild

C02 Roman Vale
- planning/source: C02
- role: primary antagonist / system architect
- action: already in key-character batch; later audit only

C03 Birta
- planning: C03
- source-truth: C23
- role: domestic/supporting anchor
- action: already in key-character batch; later scene-specific use if needed

C04 Dimitri Koss
- planning: C04
- source-truth: C06
- role: operational antagonist support / enforcer-rival
- action: already in key-character batch; later audit only

C05 Marcus Chen
- planning: C05
- source-truth: C03
- role: catalyst / ghost
- action: already in key-character batch; later audit only

The Herald / Halo Unit
- source-truth: C05
- planning record: not yet compacted
- role: system antagonist / broadcast presence / pressure instrument
- action: create character-like system element

Zara Okonkwo
- source-truth: C04
- planning record: not yet compacted
- role: primary ally / emotional B-story
- action: source intake + visual scaffold

Jin Vale
- source-truth: C12
- planning record: not yet compacted
- role: emotional objective
- action: protected-subject visual scaffold

Sera / Seraphina Mast
- source-truth: C07
- planning record: not yet compacted
- role: media ally / publication arc
- action: source intake + visual scaffold
```

### Critical Invariant

```text
All production records use compact planning IDs.
Source-truth IDs remain only in source_truth_reference fields and documentation.
Do not create duplicate characters when source ID and compact planning ID differ.
```

---

## 6. Phase 2 — C01 Nadia Clean v2 Rebuild

C01 will be rebuilt cleanly under v2, but old C01 records remain untouched.

### Key Rule

```text
Existing C01 / SC0001 / TAKE002 chain remains untouched.
New C01 v2 is created as a separate look/reference chain.
```

### PR-C01-1 — Scaffold

```text
chore(c01): scaffold clean Nadia v2 reference chain
```

Recommended look ID:

```text
C01_NADIA_CANON_V2
```

or scene-specific:

```text
C01_HOME_MORNING_V2
```

Files:

```text
visual_dev/elements/characters/C01/look_variants/C01_NADIA_CANON_V2/reference_chain.yaml
visual_dev/elements/characters/C01/look_variants/C01_NADIA_CANON_V2/gpt_images_perspective_pack.yaml
```

Stage structure:

```text
MJ V8.1 narrative identity reference
→ MJ V7 --oref refinement
→ GPT Images 2:
   front_reference
   three_quarter_medium_reference
   three_quarter_close_reference
```

### PR-C01-2 — Visual Registration

```text
chore(c01): register clean Nadia v2 visual references
```

Scope:

```text
Stage 1 selected external ref
Stage 2 selected external ref
GPT Images 2 three-view outputs
QC report
local media index
kling_element_reference
```

Do not:

```text
modify old C01 v1 files
migrate @Nadia alias
mutate SC0001 selected take
```

Alias migration, if needed later:

```text
chore(c01): migrate @Nadia alias to clean v2 reference
```

---

## 7. Phase 3 — The Herald / Halo Unit

The Halo Unit is not treated as a simple prop. It is a **character-like system embodiment**.

### Model

```text
The Herald = persona / voice / broadcast intelligence
Halo Unit = physical robotic body / on-screen embodiment
Oracle Prime = platform/system
```

### PR-HALO-1 — Scaffold

```text
schema(elements): scaffold Herald Halo Unit as character-like system element
```

Suggested path:

```text
visual_dev/elements/system_characters/HERALD_HALO/
```

If repo requires additive schemas:

```text
schemas/system_character_element.schema.json
schemas/system_character_reference_chain.schema.json
validate_production_records.py registration
```

Files:

```text
identity_plan.yaml
reference_chain.yaml
gpt_images_perspective_pack.yaml
```

### PR-HALO-2 — Visual Production

```text
chore(herald): register Halo Unit visual identity references
```

Production model:

```text
GPT Images 2 first reference
→ GPT Images 2 scale-angle pack:
   front_reference
   three_quarter_medium_reference
   three_quarter_close_reference
→ QC
→ Kling reference
```

Prompt invariants:

```text
near-future but not sci-fi fantasy
service-robot / broadcast-surveillance body
sensor array as attention substitute
warm companion tone hiding control
no cute robot
no humanoid face unless source later demands it
no logo/text/watermark
```

---

## 8. Phase 4 — Zara Okonkwo

### PR-ZARA-1 — Source Intake

```text
chore(characters): add Zara source-truth visual scaffold
```

Rules:

```text
source_truth_reference.source_character_id: C04
compact planning ID: next available ID
do not reuse compact C04 because C04 is Dimitri
```

Files:

```text
planning/characters/<next_compact_id>.yaml
planning/manifests/character_index.csv
visual_dev/elements/characters/<next_compact_id>/reference_chain.yaml
visual_dev/elements/characters/<next_compact_id>/gpt_images_perspective_pack.yaml
```

### PR-ZARA-2 — Visual Production

```text
chore(zara): register Zara v2 visual references
```

Pipeline:

```text
MJ V8.1 narrative identity
→ MJ V7 --oref refinement
→ GPT Images 2 scale-angle pack
→ QC
→ Kling reference
```

---

## 9. Phase 5 — Jin Vale

Jin is a protected subject / emotional objective, not a normal action-performance character.

### PR-JIN-1 — Scaffold

```text
chore(characters): add Jin Vale protected-subject visual scaffold
```

Rules:

```text
source_truth_reference.source_character_id: C12
compact planning ID: next available ID
```

Prompt/QC principles:

```text
infant safety
ordinary human warmth
protected subject presence
no distress exploitation
no action posing
care context only if source-required
medical bracelet continuity may become separate prop
```

### PR-JIN-2 — Visual Production

```text
chore(jin): register Jin Vale protected-subject visual references
```

---

## 10. Phase 6 — Sera / Seraphina Mast

### PR-SERA-1 — Source Intake

```text
chore(characters): add Sera visual planning scaffold
```

Rules:

```text
source_truth_reference.source_character_id: C07
compact planning ID: next available ID
```

### PR-SERA-2 — Visual Production

```text
chore(sera): register Sera v2 visual references
```

Pipeline:

```text
MJ V8.1 narrative identity
→ MJ V7 --oref refinement
→ GPT Images 2 scale-angle pack
→ QC
→ Kling reference
```

---

## 11. Phase 7 — Golden Scene Selection

After character readiness phases, select the golden scene.

### PR-GOLDEN-0

```text
docs(golden): evaluate candidate scenes for full reference production
```

Selection criteria:

```text
Nadia central?
The Herald / Halo Unit pressure?
Roman / Dimitri / Zara / Jin / Sera required?
Dialogue?
Camera movement and shot coverage potential?
Insert/detail/reaction/final hold?
Element readiness complete?
```

Candidate categories:

```text
A) SC0001 domestic opening
B) First broadcast / Halo Unit confrontation
C) VELTAIN / Jin recovery or climax
D) Zara alliance turning point
E) Sera publication / evidence leak
```

The PR must end with a single selected scene.

---

## 12. Phase 8 — Full Golden Reference Scene Production

Milestone:

```text
v0.18.0-golden-reference-scene
```

### PR-GOLDEN-1 — Golden Scene Plan

```text
feat(golden): add golden reference scene production plan
```

File:

```text
planning/scenes/<SCENE_ID>/golden_reference_plan.yaml
```

### PR-GOLDEN-2 — Shot Manifests

```text
feat(golden): add shot element manifests for selected scene
```

Path:

```text
visual_dev/omni_sets/<SCENE_ID>/shot_element_manifests/SH001.yaml
visual_dev/omni_sets/<SCENE_ID>/shot_element_manifests/SH002.yaml
...
```

Coverage:

```text
SH001 establishing
SH002 character entrance
SH003 primary dialogue / system pressure
SH004 reaction close
SH005 insert/detail
SH006 movement transition
SH007 final hold
```

### PR-GOLDEN-3 — Kling Prompt Records

```text
chore(golden): add alias-only Kling prompts for selected scene shots
```

Rules:

```text
prompt_text uses only registered @aliases
no canonical IDs
no raw character full names
dialogue comes from dialogue_beats only when native_audio_readiness == ready
otherwise dialogue lines are omitted
```

### PR-GOLDEN-4 — External Generation Metadata

```text
chore(golden): register Kling draft take metadata for selected scene
```

No binary commits.

### PR-GOLDEN-5 — QC

```text
review(golden): add video/audio QC for selected scene takes
```

### PR-GOLDEN-6 — Selected Takes

```text
chore(golden): select golden scene takes
```

### PR-GOLDEN-7 — Assembly Metadata

```text
chore(golden): add golden scene assembly metadata
```

Files:

```text
evidence/scene_clip_map.csv
planning/scenes/<SCENE_ID>/golden_scene_assembly.yaml
evidence/operator_sessions/OP-GOLDEN-<SCENE_ID>-*.yaml
```

Final tag:

```text
v0.18.0-golden-reference-scene
```

---

## 13. Global Production Rules

```text
No binary image/video/audio committed.
All media external refs only.
Schema changes additive only.
No existing C01 / SC0001 / TAKE002 chain mutation.
No lifecycle promotion without explicit human approval.
All prompt_text fields use alias-only discipline.
Dialogue renders only when native_audio_readiness is ready.
Scene looks are separate look variants, not character redesigns.
Golden scene is shot-based, not one giant prompt.
Force-push to main never used.
--no-verify never used.
Separate PRs per scope.
```

---

## 14. Validation Per PR

Every PR must run:

```bash
python scripts/validate_production_records.py --repo-root .
python -m pytest -q
```

When touching scene readiness:

```bash
python scripts/agents/scene_readiness.py --scene <SCENE_ID>
```

PR descriptions must include validation counts.

---

## 15. Final Execution Order

```text
0. PR-BATCH-KEYCHAR-1 — register C02/C03/C04/C05 visual batch
1. Optional private tag — v0.17.1-key-character-visual-batch
2. PR-CHAR-0 — visual priority roadmap
3. PR-C01-1 — C01 clean v2 scaffold
4. PR-C01-2 — C01 clean v2 visual registration
5. PR-HALO-1 — Herald / Halo Unit system-character scaffold
6. PR-HALO-2 — Halo Unit visual registration
7. PR-ZARA-1 — Zara source intake
8. PR-ZARA-2 — Zara visual production
9. PR-JIN-1 — Jin protected-subject scaffold
10. PR-JIN-2 — Jin visual production
11. PR-SERA-1 — Sera source intake
12. PR-SERA-2 — Sera visual production
13. PR-GOLDEN-0 — golden scene candidate analysis
14. PR-GOLDEN-1..7 — full golden scene production
15. tag v0.18.0-golden-reference-scene
```

---

## 16. Immediate Next Action

Open the batch PR first:

```text
chore(characters): register key character v2 visual batch
```

Include only:

```text
C02 Roman Vale
C03 Birta
C04 Dimitri Koss
C05 Marcus Chen
```

After it merges, continue with the new production phases.
