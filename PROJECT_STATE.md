# PROJECT_STATE.md â€” Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## ğŸ‡¹ğŸ‡· Åu An Neredeyiz (TÃ¼rkÃ§e Ã–zet)

Milestone M5’teyiz. **C07 Sera + C11 Halo Unit scaffold tamamlandı (2026-06-19):**
C01-C10 tümü `binding: created`. C11 Halo Unit (Herald robot gövdesi) Stage-1
scaffold hazır — MJ v8.1 batch koşulmayı bekliyor (SC0018, seed 728463).
**Sıradaki:** (1) SC0014 v07 klip QC — operatör izleyip skor vermeli; (2) C11 Halo Unit
MJ Stage-1 batch → hero seç → Stage-2/3 pipeline.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 â€” character visual element pipeline |
| Last updated | 2026-06-19 |
| Public checkpoint | v0.18.0 (Zenodo DOI: 10.5281/zenodo.20735582) |

## Character Pipeline (C01–C11)

<!-- AUTO:PIPELINE:START -->
Stages: S1 = MJ v8.1 hero · S2 = MJ v7 --oref identity lock · S3 = four-view pack · Binding = lifecycle status

| ID | Name | S1 | S2 | S3 | Binding | Scene(s) | Notes |
|---|---|---|---|---|---|---|---|
| C01 | Nadia Vale | ✅ | ✅ | ✅ | **created** | SC0014, SC0047, SC0089, SC0111 | 4 look bindings created: base, field-night, transit, battle-worn |
| C02 | Roman Vale | ✅ | ✅ | ✅ | **created** | SC0111 |  |
| C03 | Birta | ✅ | ✅ | ✅ | **created** | SC0001 | KER_C03_DOMESTIC_ROUTINE_V001 locked; PQC ≥89 all views |
| C04 | Dimitri | ✅ | ✅ | ✅ | **created** | SC0014 |  |
| C05 | Marcus | ✅ | ✅ | ✅ | **created** | SC0004 (phys) / SC0047 (VO) | KER_C05_PRIVATE_MEETING_V001 locked; PQC ≥90 all views |
| C06 | Zara | ✅ | ✅ | ✅ | **created** | SC0089 |  |
| C07 | Sera | ✅ | ✅ | ✅ | **created** | SC0040 | KER_C07_NEWSROOM_V001 locked; PQC ≥92 all views |
| C08 | Jin | ✅ | ✅ | ✅ | **created** | SC0014 |  |
| C09 | Otto | ✅ | ✅ | ✅ | **created** | SC0047 |  |
| C10 | Carrier+Holder | ✅ | ✅ | ✅ | **created** | SC0014 | Two enforcer figures (Carrier + Holder), per-figure packs |
| C11 | Halo Unit | ⏳ | — | — | scaffold | SC0016, SC0018, SC0095 | Non-human robot body; Stage-1 MJ batch koşulmayı bekliyor (seed 728463) |
<!-- AUTO:PIPELINE:END -->

## Active Scene Work

- **SC0014 v07 text-only literal paket hazÄ±r** (Anchor & Animate emekli):
  8 `text_only` Kling promptu (`SC0014__omni-kling-omni-clip-clip-sc0014-01..08-safe__v07`),
  `language_profile: kling_literal_alias_locked`. 8 manifest + ledger literal `render_*`
  alanlarÄ± taÅŸÄ±yor (ÅŸiirsel alanlar korundu, modele basÄ±lmÄ±yor). CLIP 01 reveal'lÄ±
  (Nadia+Jin); v06'nÄ±n 22 still + 8 contact + 8 anchored kaydÄ± + library/map satÄ±rlarÄ±
  deprecated. C08 gate korunuyor. 8 klip operatÃ¶r tarafÄ±ndan Kling'de Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± ve
  `archive/closing_price/SC0014/clips/` altÄ±na arÅŸivlendi (git-ignored; index:
  `LOCAL_MEDIA_INDEX_SC0014_ARCHIVE_V001.yaml`, kind `kling_omni_v07_text_only_take`).
  QC/seÃ§im henÃ¼z yapÄ±lmadÄ±. **OperatÃ¶r sÄ±rasÄ±:** klipleri izle â†’ her klip iÃ§in
  status + 5 kalite skoru ver â†’ `review-video-takes` Ã§alÄ±ÅŸtÄ±r.
- Golden scenes referenced by created bindings: **SC0014, SC0047, SC0089, SC0111**.
- Golden scene **SC0001** queued in the revised plan (after character batch).

## Next Steps (priority order)

1. **SC0014 video take QC (v07)** â€” 8 klip arÅŸivlendi (QC bekliyor). OperatÃ¶r her klip iÃ§in status (selected/candidate/rejected/needs_revision) + 5 kalite skoru (identity_consistency, source_grounding, style_compliance, continuity, production_usability, 1-5) versin â†’ `review-video-takes` Ã§alÄ±ÅŸtÄ±rÄ±lÄ±p `video_takes.yaml` yazÄ±lacak. Final pass iÃ§in gerekirse `continuity_seed_ref` (extracted last-frame). (operator-driven)
2. ~~SC0047/SC0089 t2i oref schema drift~~ â€” **Ã§Ã¶zÃ¼ldÃ¼ 2026-06-16**: 3 kÃ¶k alan `generation_params` iÃ§ine taÅŸÄ±ndÄ±, validator 55/55 temiz.
3. ~~LOC005/006/007/PROP008 lifecycle promotion~~ â€” **tamamlandÄ± 2026-06-17**: binding_status plannedâ†’created; @LOC005_CORRIDOR, @LOC006_QUAY, @LOC007_ANTECHAMBER, @PROP008_HANDSET alias baÄŸlandÄ±.
4. ~~SC0047/SC0089/SC0111 Kling Omni clip planÄ±~~ â€” **tamamlandÄ± 2026-06-17**: 40 v07 prompt kaydÄ±; 3 inject scripti + validate 95/95.
4. ~~PR-BATCH-KEYCHAR-1~~ — **tamamlandı 2026-06-18**: C03 Birta + C05 Marcus binding created; KER_C03_DOMESTIC_ROUTINE_V001 + KER_C05_PRIVATE_MEETING_V001 locked.
5. **C11 Halo Unit** — Stage-1 scaffold hazır (2026-06-19). Operatör: MJ'de `SC0018__t2i-char-c11-identity-mj-v8__v01` batch çalıştır → en iyi robot gövde tasarımını seç (sensor dome netliği, chassis silüeti, near-future estetik) → hero paylaş → Stage-2/3 pipeline.

## Known Issues / Blockers

From `closingpriceclaudecodeanalysisforcode.md` (multi-agent analysis, 2026-06-08/09):

- **36 thin dossiers**: C13â€“C48 have only one-line descriptions â€” LLM is blind
  on them during draft generation.
- **6 missing contract fields** across all 120 scene contracts
  (opposition_escalation, cause_from_previous, effect_on_next,
  value_shift_evidence_target, relational_stakes, character_state_change) â€”
  schema exists, contract files not yet populated.
- **turn_trigger rule contradiction**: anti-clichÃ© rule contradicts its own
  example table.
- **Emotional trajectory layer** locks the LLM to the known ending (misses
  moment-to-moment discovery).

## Session Log (newest first, keep ~10 lines)

<!-- AUTO:SESSION_LOG:START -->
- 2026-06-19 — chore(M5): C11 Halo Unit Stage-1 scaffold — character record (C11) + identity_anchor + MJ v8.1 prompt SC0018 (seed 728463)
- 2026-06-18 — feat(M5): C07 Sera binding created — Stage-3 PQC >=92, KER_C07_NEWSROOM_V001 locked
- 2026-06-18 — feat(M5): C07 Sera Stage-2 lock selected (9fcba347_3); identity_anchor stage2_selected
- 2026-06-18 — feat(M5): C07 Sera Stage-1 hero selected (2c0bb89d_1); Stage-2 oref URL recorded; --oref prompt drafted
- 2026-06-18 — chore(M5): C07 Sera Stage-1 scaffold — identity_anchor stub + MJ v8.1 prompt (SC0040, seed 514637)
- 2026-06-18 — feat(M5): C05 Marcus binding created — Stage-3 PQC >=90, KER_C05_PRIVATE_MEETING_V001 locked
- 2026-06-18 — feat(M5): C03 Birta binding created — Stage-3 PQC >=89, KER_C03_DOMESTIC_ROUTINE_V001 locked
- 2026-06-18 — feat(M5): PR-BATCH-KEYCHAR-1 Stage-2 lock + Stage-3 PPACK (C03/C05); archive paths fixed to closing_price
- 2026-06-18 — chore(archive): rename archive path nexuszero â†’ closing_price
- 2026-06-17 — chore(citation): point CITATION metadata to v0.18.0 DOI 10.5281/zenodo.20735582
- 2026-06-17 — fix(lint): reindent SC0014 manifests + omni_clip_plan for yamllint compliance
- 2026-06-17 — chore(manifests): rebuild planning manifests â€” M5 pipeline additions (C09, LOC005/006/007, WD008-014, PROP007/008, SC0014/0047/0089/0111)
- 2026-06-17 — chore(merge): resolve conflict â€” keep clean-slate teardown deletions (LOC001/PROP003 V002 image_selection)
- 2026-06-17 — chore(release): v0.18.0 release artifacts â€” CHANGELOG + PROJECT_STATE update
- 2026-06-17 — [fix] operator session schema â€” remove extra fields, add required recommended_steps
- 2026-06-17 — promote @LOC005_CORRIDOR/@LOC006_QUAY/@LOC007_ANTECHAMBER/@PROP008_HANDSET to created (SC0047/SC0089/SC0111, QC>=85)
- 2026-06-17 — lock LOC005/006/007/PROP008 three-view packs + KER records (QC>=85); promote pending human PR
- 2026-06-17 — [fix] SC0047/SC0089 oref schema drift + archive LOC005/006/007/PROP008 stage-1 first-refs
<!-- AUTO:SESSION_LOG:END -->
