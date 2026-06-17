# PROJECT_STATE.md — Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## 🇹🇷 Şu An Neredeyiz (Türkçe Özet)

Milestone M5'teyiz. **SC0014 v07 TAMAMLANDI (2026-06-16):** Anchor & Animate (22 still + contact-sheet
+ `anchored_i2v`) rotası emekliye ayrıldı; yerine **text_only literal multi-shot** geldi
(`language_profile: kling_literal_alias_locked`). Kök sorun çözüldü: kötü dil (metafor, "infant/mother",
serbest "center") renderer'da değil kanonik YAML'daydı — **dual-field split** ile şiirsel alanlar insana
kaldı, modele yalnız yeni literal `render_*` alanları basılıyor. 8 klibe literal render_* yazıldı;
**CLIP 01 artık boş oda ile bitmiyor, aynı klipte @C01_NADIA + @C08_JIN reveal ediliyor**; CLIP 02
"aniden insanlar" hissini kaldırdı. 8 v07 kayıt üretildi (`...-safe__v07`), v06'nın 38 satırı (still/
contact/anchored) deprecated. Validator katı banları zorluyor (raw isim / role noun / metafor / bare
center; alias+diyalog maskeli); aktif Kling kaydı `language_profile` bildirmek zorunda; `text_only`
altında anchored üçlüsü yasak. Test: 1520 geçti / 3 atlandı (12 yeni v07 testi). Kling'e canlı çağrı yok.
**2026-06-16 operatör üretimi:** Operatör 8 klibi Kling'de text_only çalıştırdı; 8 .mp4 lokal olarak
`archive/nexuszero/SC0014/clips/` altına arşivlendi (git-ignored) ve
`evidence/local_media_indices/LOCAL_MEDIA_INDEX_SC0014_ARCHIVE_V001.yaml`'e metadata-only kayıt
girildi (`kling_omni_v07_text_only_take`, take_id `CLIP_SC0014_0N_v07_take01`). QC/seçim henüz
yapılmadı — Batch 8.5 `review-video-takes` akışı (status + 5 kalite skoru) bekliyor.
**Operatör sırası:** Klipleri izle → her klip için status/kalite skoru ver → `review-video-takes`
çalıştır (`video_takes.yaml` + review notes).
**2026-06-16 oref schema drift düzeltildi:** SC0047/SC0089 Stage-2 `--oref` lock kayıtlarında
kök seviyede duran `oref_source_id`/`oref_source_external_ref`/`oref_cdn_url` alanları
`prompt_record` şemasında tanımsızdı (root `additionalProperties: false`); üç alan
`generation_params` içine taşındı (o blok `additionalProperties: true`). Hiçbir kod bu
alanları kök seviyede okumuyordu, taşıma güvenli. `validate_prompt_records.py`: 55/55 temiz.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 — character visual element pipeline |
| Last updated | 2026-06-17 |
| Public checkpoint | v0.17.0 (Zenodo DOI: 10.5281/zenodo.20241807) |

## Character Pipeline (C01–C10)

<!-- AUTO:PIPELINE:START -->
Stages: S1 = MJ v8.1 hero · S2 = MJ v7 --oref identity lock · S3 = four-view pack · Binding = lifecycle status

| ID | Name | S1 | S2 | S3 | Binding | Scene(s) | Notes |
|---|---|---|---|---|---|---|---|
| C01 | Nadia Vale | ✅ | ✅ | ✅ | **created** | SC0014, SC0047, SC0089, SC0111 | 4 look bindings created: base, field-night, transit, battle-worn |
| C02 | Roman Vale | ✅ | ✅ | ✅ | **created** | SC0111 |  |
| C03 | Birta | — | — | — | — | — | Needs PR-BATCH-KEYCHAR-1 registration |
| C04 | Dimitri | ✅ | ✅ | ✅ | **created** | SC0014 |  |
| C05 | Marcus | ✅ | ✅ | ✅ | **created** | SC0047 | Needs PR-BATCH-KEYCHAR-1 registration |
| C06 | Zara | ✅ | ✅ | ✅ | **created** | SC0089 |  |
| C07 | Sera | — | — | — | — | — | Queued after key-character batch |
| C08 | Jin | ✅ | ✅ | ✅ | **created** | SC0014 |  |
| C09 | Otto | ✅ | ✅ | ✅ | **created** | SC0047 |  |
| C10 | Carrier+Holder | ✅ | ✅ | ✅ | **created** | SC0014 | Two enforcer figures (Carrier + Holder), per-figure packs |
<!-- AUTO:PIPELINE:END -->

## Active Scene Work

- **SC0014 v07 text-only literal paket hazır** (Anchor & Animate emekli):
  8 `text_only` Kling promptu (`SC0014__omni-kling-omni-clip-clip-sc0014-01..08-safe__v07`),
  `language_profile: kling_literal_alias_locked`. 8 manifest + ledger literal `render_*`
  alanları taşıyor (şiirsel alanlar korundu, modele basılmıyor). CLIP 01 reveal'lı
  (Nadia+Jin); v06'nın 22 still + 8 contact + 8 anchored kaydı + library/map satırları
  deprecated. C08 gate korunuyor. 8 klip operatör tarafından Kling'de çalıştırıldı ve
  `archive/nexuszero/SC0014/clips/` altına arşivlendi (git-ignored; index:
  `LOCAL_MEDIA_INDEX_SC0014_ARCHIVE_V001.yaml`, kind `kling_omni_v07_text_only_take`).
  QC/seçim henüz yapılmadı. **Operatör sırası:** klipleri izle → her klip için
  status + 5 kalite skoru ver → `review-video-takes` çalıştır.
- Golden scenes referenced by created bindings: **SC0014, SC0047, SC0089, SC0111**.
- Golden scene **SC0001** queued in the revised plan (after character batch).

## Next Steps (priority order)

1. **SC0014 video take QC (v07)** — 8 klip arşivlendi (QC bekliyor). Operatör her klip için status (selected/candidate/rejected/needs_revision) + 5 kalite skoru (identity_consistency, source_grounding, style_compliance, continuity, production_usability, 1-5) versin → `review-video-takes` çalıştırılıp `video_takes.yaml` yazılacak. Final pass için gerekirse `continuity_seed_ref` (extracted last-frame). (operator-driven)
2. ~~SC0047/SC0089 t2i oref schema drift~~ — **çözüldü 2026-06-16**: 3 kök alan `generation_params` içine taşındı, validator 55/55 temiz.
3. ~~LOC005/006/007/PROP008 lifecycle promotion~~ — **tamamlandı 2026-06-17**: binding_status planned→created; @LOC005_CORRIDOR, @LOC006_QUAY, @LOC007_ANTECHAMBER, @PROP008_HANDSET alias bağlandı.
4. **SC0047/SC0089/SC0111 Kling Omni clip planı** — element binding'ler hazır; SC0014 v07 akışı (text_only literal, kling_literal_alias_locked) model olarak alınarak 3 sahne için manifest + ledger + prompt kayıtları üretilecek.
4. **PR-BATCH-KEYCHAR-1** — C03 Birta + C05 Marcus pre-checkpoint registration.
5. **C07 Sera** + **Halo Unit** element production.

## Known Issues / Blockers

From `closingpriceclaudecodeanalysisforcode.md` (multi-agent analysis, 2026-06-08/09):

- **36 thin dossiers**: C13–C48 have only one-line descriptions — LLM is blind
  on them during draft generation.
- **6 missing contract fields** across all 120 scene contracts
  (opposition_escalation, cause_from_previous, effect_on_next,
  value_shift_evidence_target, relational_stakes, character_state_change) —
  schema exists, contract files not yet populated.
- **turn_trigger rule contradiction**: anti-cliché rule contradicts its own
  example table.
- **Emotional trajectory layer** locks the LLM to the known ending (misses
  moment-to-moment discovery).

## Session Log (newest first, keep ~10 lines)

<!-- AUTO:SESSION_LOG:START -->
- 2026-06-17 — v0.18.0 release artifacts: CHANGELOG + RELEASE_NOTES + MANIFEST + SANITIZATION_CHECKLIST
- 2026-06-17 — [fix] operator session schema — remove extra fields, add required recommended_steps
- 2026-06-17 — promote @LOC005_CORRIDOR/@LOC006_QUAY/@LOC007_ANTECHAMBER/@PROP008_HANDSET to created (SC0047/SC0089/SC0111, QC>=85)
- 2026-06-17 — lock LOC005/006/007/PROP008 three-view packs + KER records (QC>=85); promote pending human PR
- 2026-06-17 — [fix] SC0047/SC0089 oref schema drift + archive LOC005/006/007/PROP008 stage-1 first-refs
- 2026-06-17 — archive SC0014 v07 Kling clips (8 takes, git-ignored) + add clips subdir
- 2026-06-17 — SC0014 v07 text-only literal multi-shot (kling_literal_alias_locked); Anchor & Animate retired
- 2026-06-15 — SC0014 Anchor & Animate pipeline Faz 0â€“6 (shot-photography-first)
- 2026-06-12 — SC0014 FAZ C â€” 8-clip plan + SCL ledger + 8 Format A O3 prompts (Kling ready)
- 2026-06-12 — lock PROP001 bracelet three-view + promote @PROP001_BRACELET to created (SC0014, QC>=85); SC0014 all elements created
- 2026-06-12 — lock LOC001 nursery three-view + promote @LOC001_NURSERY to created (SC0014, QC>=85)
<!-- AUTO:SESSION_LOG:END -->
