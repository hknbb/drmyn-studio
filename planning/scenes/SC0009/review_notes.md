# SC0009 — Review Notes

**Scene ID:** SC0009
**Title:** Roman Confirms the Betrayal
**Current status:** planning_review — use with caution (inferred boundary)

---

## What is confirmed

- Scene card hydrated at inferred confidence. Boundary type: dash-start / dash-end. Mapping confidence: inferred.
- Source retrieval span: lines 615–687.
- The scene opens with a carry-over aftermath beat in the anonymous room (continuing from SC0008), then cuts to Roman's Trophy Room — the first explicit in-scene slugline.
- Location: LOC001 (Roman's Trophy Room — Vale Residence). The scene card follows source authority (the explicit slugline) rather than the older Phase 2 seed-row bucket (LOC004). This conflict is documented in the planning_hydration_report.
- Time of day: NIGHT. Source-stated.
- Characters present: C01 (Nadia, carry-over beat), C02 (Marcus, carry-over beat), C05 (in trophy-room context — see review item below). Explicit dialogue: Dimitri, Roman.
- Props: PROP005. Wardrobe: WD002 (carry-over beat), WD003 (Roman's trophy room).
- Sequence/phase: SEQ01 / PH_EQUILIBRIUM / B09.
- Pilot scene review packet: `evidence/article3/pilot_scene_review_packets/SC0009.md`.
- Planning hydration report classifies this as a lower-confidence record (inferred boundary).

---

## What still needs human review

- `review_status` is `needs_human_review`. Inferred boundary requires a human to verify that the carry-over span and the trophy-room scene are correctly bucketed as one retrieval span. Verify the dash-start / dash-end boundary placement against the excerpt.
- **LOC004 vs LOC001 conflict**: The older Phase 2 seed row buckets SC0009 under LOC004, but the scene card now follows the explicit slugline (LOC001 — Roman's Trophy Room). Both the scene card and the planning hydration report document this conflict. A human reviewer should confirm the LOC001 ruling before the scene card is finalized.
- **C05 assignment conflict** (same as SC0008): `planning/characters/C05.yaml` uses `cue_name: MARCUS` and `role: CATALYST`, conflating C05 with C03 or C02. The scene card lists C05 in the trophy-room context where Dimitri is the active interlocutor. A human reviewer must resolve which compact ID covers Roman's contact Dimitri.
- PROP005 role in this scene should be confirmed against the prop record before the scene card is finalized.

---

## What waits for Stage B / Omni

- Omni schema fields are not added in Stage A.
- Trophy-room object placement, glass-case framing, and shot-list specifics are Stage B deliverables.
- LOC004 legacy bucket cleanup is deferred to Stage B.
- The C05 compact ID conflict requires a project-level policy decision before this scene card can reach `approved` status.
