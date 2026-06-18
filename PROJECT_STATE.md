# PROJECT_STATE.md â€” Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## ğŸ‡¹ğŸ‡· Åu An Neredeyiz (TÃ¼rkÃ§e Ã–zet)

Milestone M5'teyiz. **PR-BATCH-KEYCHAR-1 Stage-1 hero seÃ§imi tamamlandÄ± (2026-06-17):**
**PR-BATCH-KEYCHAR-1 Stage-2 kilidleri tamamlandÄ± (2026-06-18):** C03 Birta â†’ Stage-2
hero `0a07694e_0` (krem Ã¶nlÃ¼k, gri arka plan). C05 Marcus â†’ Stage-2 hero `e724a825_0`
(koyu gri gÃ¶mlek, nÃ¶tr arka plan). Her iki `identity_anchor.yaml` `stage2_selected`.
**Stage-3 PPACK'lar hazÄ±r:** `PPACK_C03_DOMESTIC_ROUTINE_V001` + `PPACK_C05_PRIVATE_MEETING_V001`.
OperatÃ¶r sÄ±rasÄ±: ChatGPT Images 2'ye PRIMARY (Stage-2) + SECONDARY (Stage-1) yÃ¼kle â†’
4 perspektif gÃ¶rÃ¼ntÃ¼ Ã¼ret â†’ PQC (â‰¥85) â†’ KER. **SC0047/SC0089/SC0111 Kling Omni v07**
tamamlandÄ±. SC0014 v07 hazÄ±r; 8 klip arÅŸivlendi (QC bekliyor).

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 â€” character visual element pipeline |
| Last updated | 2026-06-18 (C03/C05 Stage-2 lock + Stage-3 PPACK) |
| Public checkpoint | v0.18.0 (Zenodo DOI: 10.5281/zenodo.20735582) |

## Character Pipeline (C01â€“C10)

<!-- AUTO:PIPELINE:START -->
Stages: S1 = MJ v8.1 hero Â· S2 = MJ v7 --oref identity lock Â· S3 = four-view pack Â· Binding = lifecycle status

| ID | Name | S1 | S2 | S3 | Binding | Scene(s) | Notes |
|---|---|---|---|---|---|---|---|
| C01 | Nadia Vale | âœ… | âœ… | âœ… | **created** | SC0014, SC0047, SC0089, SC0111 | 4 look bindings created: base, field-night, transit, battle-worn |
| C02 | Roman Vale | âœ… | âœ… | âœ… | **created** | SC0111 |  |
| C03 | Birta | âœ… | âœ… | â€” | â€” | SC0001 | Stage-2 lock selected (0a07694e_0); Stage-3 PPACK ready |
| C04 | Dimitri | âœ… | âœ… | âœ… | **created** | SC0014 |  |
| C05 | Marcus | âœ… | âœ… | â€” | â€” | SC0004 (phys) / SC0047 (VO) | Stage-2 lock selected (e724a825_0); Stage-3 PPACK ready |
| C06 | Zara | âœ… | âœ… | âœ… | **created** | SC0089 |  |
| C07 | Sera | â€” | â€” | â€” | â€” | â€” | Queued after key-character batch |
| C08 | Jin | âœ… | âœ… | âœ… | **created** | SC0014 |  |
| C09 | Otto | âœ… | âœ… | âœ… | **created** | SC0047 |  |
| C10 | Carrier+Holder | âœ… | âœ… | âœ… | **created** | SC0014 | Two enforcer figures (Carrier + Holder), per-figure packs |
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
4. **PR-BATCH-KEYCHAR-1** â€” Stage-3 hazÄ±r. **OperatÃ¶r**: ChatGPT Images 2'ye her karakter iÃ§in PRIMARY (Stage-2 lock) + SECONDARY (Stage-1 hero) yÃ¼kle â†’ PPACK prompt metinlerini sÄ±rayla Ã§alÄ±ÅŸtÄ±r â†’ 4 perspektif gÃ¶rÃ¼ntÃ¼ Ã¼ret â†’ PQC â†’ KER â†’ binding 'created'.
5. **C07 Sera** + **Halo Unit** element production.

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
- 2026-06-18 â€” feat(M5): PR-BATCH-KEYCHAR-1 Stage-2 lock + Stage-3 PPACK â€” C03 Birta (0a07694e_0) + C05 Marcus (e724a825_0); look_variants + perspective_packs oluÅŸturuldu
- 2026-06-17 â€” feat(M5): PR-BATCH-KEYCHAR-1 Stage-2 --oref prompts drafted â€” C03 Birta (6acb8065) + C05 Marcus (9b0373c6); identity_anchor oref_url + prompt_ref kayÄ±tlandÄ±
- 2026-06-17 â€” feat(M5): PR-BATCH-KEYCHAR-1 Stage-1 heroes selected â€” C03 Birta eadae384_2 + C05 Marcus d246ae27_2; identity_anchor.yaml stage1_ref populated
- 2026-06-17 â€” chore(M5): PR-BATCH-KEYCHAR-1 Stage-1 scaffold â€” C03 Birta + C05 Marcus MJ prompt drafts + identity_anchor stubs; fix C05 pipeline status
- 2026-06-17 â€” feat(M5): SC0047/SC0089/SC0111 v07 Kling Omni clip plans complete (40 prompts, 3 inject scripts, 95/95 valid)
- 2026-06-17 â€” chore(citation): point CITATION metadata to v0.18.0 DOI 10.5281/zenodo.20735582
- 2026-06-17 â€” fix(lint): reindent SC0014 manifests + omni_clip_plan for yamllint compliance
- 2026-06-17 â€” chore(manifests): rebuild planning manifests Ã¢â‚¬â€ M5 pipeline additions (C09, LOC005/006/007, WD008-014, PROP007/008, SC0014/0047/0089/0111)
- 2026-06-17 â€” chore(merge): resolve conflict Ã¢â‚¬â€ keep clean-slate teardown deletions (LOC001/PROP003 V002 image_selection)
- 2026-06-17 â€” chore(release): v0.18.0 release artifacts Ã¢â‚¬â€ CHANGELOG + PROJECT_STATE update
- 2026-06-17 â€” [fix] operator session schema Ã¢â‚¬â€ remove extra fields, add required recommended_steps
- 2026-06-17 â€” promote @LOC005_CORRIDOR/@LOC006_QUAY/@LOC007_ANTECHAMBER/@PROP008_HANDSET to created (SC0047/SC0089/SC0111, QC>=85)
- 2026-06-17 â€” lock LOC005/006/007/PROP008 three-view packs + KER records (QC>=85); promote pending human PR
- 2026-06-17 â€” [fix] SC0047/SC0089 oref schema drift + archive LOC005/006/007/PROP008 stage-1 first-refs
- 2026-06-17 â€” archive SC0014 v07 Kling clips (8 takes, git-ignored) + add clips subdir
<!-- AUTO:SESSION_LOG:END -->
