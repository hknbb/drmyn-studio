# SC0008 — Review Notes

**Scene ID:** SC0008
**Title:** Marcus and Nadia's Last Night Together
**Current status:** planning_review — use with caution (inferred boundary)

---

## What is confirmed

- Scene card hydrated at inferred confidence. Boundary type: dash-start / dash-end. Mapping confidence: inferred.
- Source retrieval span: lines 530–611.
- The scene opens with a Roman carry-over beat from SC0007's office aftermath before settling into the Marcus/Nadia anonymous-room night. Both spans are within this retrieval boundary.
- Location: LOC004 (Anonymous Room). Roman is physically present only in the opening carry-over beat; Dimitri is mentioned there but not physically present in this retrieval span.
- Time of day: NIGHT. Source-stated.
- Characters present: C01 (Nadia), C02 (Marcus), C05 (in carry-over beat context — see review item below). Explicit dialogue: Marcus, Nadia.
- Wardrobe: WD002. No tracked props.
- Sequence/phase: SEQ01 / PH_EQUILIBRIUM / B08.
- Pilot scene review packet: `evidence/article3/pilot_scene_review_packets/SC0008.md`.
- Planning hydration report classifies this as a lower-confidence record (thinner source evidence at the retrieval boundary).

---

## What still needs human review

- `review_status` is `needs_human_review`. Inferred boundary requires a human to verify that the Roman carry-over beat and the Marcus/Nadia night scene are correctly bucketed as one retrieval span. Verify the dash-start / dash-end boundary is placed correctly.
- **C05 assignment conflict**: `planning/characters/C05.yaml` carries a known ID-drift conflict — the record uses `cue_name: MARCUS` and `role: CATALYST`, which aligns with C03, not C05. The scene card lists C05 in `characters_present` in the context of the carry-over beat involving Dimitri. A human reviewer must confirm which compact ID covers Dimitri's role in this span and resolve the C05/C03 drift before this scene card is finalized.
- LOC004 is a conservative anonymous-room bucket. Confirm whether the anonymous-room location needs disambiguation in a Stage B location pass.

---

## What waits for Stage B / Omni

- Omni schema fields are not added in Stage A.
- Intimate framing specifics, negative-space composition notes, and ceiling two-shot coverage details are Stage B deliverables.
- LOC004 taxonomy disambiguation is deferred to Stage B.
- The C05 compact ID conflict requires a project-level policy decision before this scene card can reach `approved` status.
