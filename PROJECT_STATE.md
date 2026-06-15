# PROJECT_STATE.md — Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## 🇹🇷 Şu An Neredeyiz (Türkçe Özet)

Milestone M5'teyiz: SC0014 **Anchor & Animate** v06 paketi tamamlandı (Faz 0-5).
**Faz 5 TAMAMLANDI (2026-06-15):** 22 shot still + 8 contact-sheet + 8 anchored_i2v Kling promptu
`prompts/draft/`'a yazıldı; v05 text-only set supersede edildi (8 dosya silindi, KO_0006 run kayıtları
temizlendi, `scene_prompt_map.csv` + `prompt_library.yaml` 38 yeni v01 kayıtla güncellendi).
Anchored paketin kalbinde: her shot ChatGPT Images 2'de fotoğraflanır → per-clip contact sheet →
Kling `anchored_i2v` (start-frame + element refs + kısa metin <2500; pass-1 frame-chain aktif).
**Faz 6 TAMAMLANDI (2026-06-15):** `docs/operator_guides/shot_photography_contact_sheet.md` yazıldı;
CI'ya 2 yeni test dosyası eklendi (`test_kling_omni_anchored_i2v.py` + `test_shot_still_coverage.py`);
memory güncellendi. Anchor & Animate mimarisi (Faz 0-6) tüm fazlarıyla teslim edildi.
**Operatör sırası:** 22 still üret → arşivle → contact sheet → 8 Kling anchored_i2v clip.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 — character visual element pipeline |
| Last updated | 2026-06-15 |
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
| C05 | Marcus | — | — | — | — | — | Needs PR-BATCH-KEYCHAR-1 registration |
| C06 | Zara | ✅ | ✅ | ✅ | **created** | SC0089 |  |
| C07 | Sera | — | — | — | — | — | Queued after key-character batch |
| C08 | Jin | ✅ | ✅ | ✅ | **created** | SC0014 |  |
| C09 | Otto | ✅ | ✅ | ✅ | **created** | SC0047 |  |
| C10 | Carrier+Holder | ✅ | ✅ | ✅ | **created** | SC0014 | Two enforcer figures (Carrier + Holder), per-figure packs |
<!-- AUTO:PIPELINE:END -->

## Active Scene Work

- **SC0014** Anchor & Animate **v06 anchored paketi hazır** (Faz 0-5 tamamlandı):
  22 shot still prompts (SC0014__still-01..22__v01) + 8 contact-sheet prompts
  (SC0014__contact-clip-01..08__v01) + 8 anchored_i2v Kling prompts
  (SC0014__omni-kling-omni-clip-clip-sc0014-01..08-safe__v01). Pass-1 frame-chain aktif:
  her clip start-frame = önceki clip'in son shot stilli. C08 gate korunuyor. v05 text-only
  set supersede edildi. **Operatör sırası:** 22 still üret → arşivle → contact sheet →
  Kling'e anchored_i2v olarak çalıştır.
- Golden scenes referenced by created bindings: **SC0014, SC0047, SC0089, SC0111**.
- Golden scene **SC0001** queued in the revised plan (after character batch).

## Next Steps (priority order)

1. **SC0014 Faz 6** — `docs/operator_guides/shot_photography_contact_sheet.md` + CI (pytest yolları + contact_sheets glob) + memory update. (NEXT metadata)
2. **SC0014 operatör üretim döngüsü** — 22 still üret (ChatGPT Images 2 w/ element refs) → arşivle (`--subdir shots`) → 8 contact-sheet → 8 anchored_i2v Kling clip. (operator-driven)
3. **SC0089, SC0047, SC0111 element pipeline** — remaining locations + props (first-ref → 3-view → KER → created).
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
- 2026-06-15 — SC0014 Anchor & Animate Faz 6: shot_photography_contact_sheet.md + CI (2 yeni test dosyası) + memory; TÜM FAZLAR (0-6) tamamlandı
- 2026-06-15 — SC0014 Anchor & Animate Faz 3-5: archive_media --subdir + anchored_i2v adapter + validate_shot_still_coverage (Faz 3-4); 22 still + 8 contact-sheet + 8 Kling anchored_i2v promptu üretildi; v05 supersede + dangling-ref temizliği; 1508 test yeşil (Faz 5)
- 2026-06-15 — SC0014 Anchor & Animate Faz 0: GPT Image 2 (≤16 giriş/≤10 çıkış/50MB) + Kling anchored_i2v snapshot'ları kilitlendi (20260615); K1-K4 kararları OP-2026-06-15-SC0014-anchor-animate-faz0'da kayıtlı; model guide'lar güncellendi (chatgpt_image 0.3.0, kling_omni 0.7.0)
- 2026-06-14 — SC0014 çekim temizlik+yeniden-üretim: 8 v05 promptu güncel manifestlerden regenere edildi (per-clip tuned negatifler geri yüklendi + 20260613 snapshot ref); commit edilmemiş v04 taslakları kaldırıldı (prompts/draft tek set: 8 v05); 131/131 valid, state_chain+continuity_presence temiz, 110 test yeşil (1 skip)
- 2026-06-14 — SC0014 Kling O3 → state-chain continuity (per-shot entry/exit_state) + per-character action; 8 manifests + ledger re-authored, 8 v05 prompts generated (v04 deprecated, evidence deduped); new validate_state_chain (render-aware); render_pass-aware 2500 cap; guide 0.6.0 + 2 rules; CI paths+pytest+blocking yamllint; CLIP_03 opening fixed (Nadia seated before men enter); 6 SC0014 validators 0 errors, all v05 <=2500
- 2026-06-14 — SC0014 v04 director pass COMPLETED: CLIP 04/07 manifests finished to v04 coverage (07 single-shot, RELEASE_AND_EXIT splittable:false); 8 v04 prompts regenerated via kling_omni adapter (Goro-style); long-form duplicate prompt files removed; C08 safe-handling language strengthened; 8-clip structure retained (coverage fills 10-13s, <=15s blocks merges); 129/129 valid, 8/8 v04 prompts valid, continuity-presence clean, 94 tests green
- 2026-06-14 — SC0014 Kling O3 → Goro-style coverage + verbatim inline dialogue (decoupled from voice gate); 8 manifests re-authored, 8 v04 prompts generated, v01/v02/v03 deleted; new validate_dialogue_coverage; renderer/planner/critic refactor green
- 2026-06-13 — SC0014 validator: validate_continuity_presence deployed (Kontrol A+B); beat plan + 7 manifests backfill; CLIP 03 v03 prompt repaired; 127/127 valid, 87/87 tests green
- 2026-06-13 — SC0014 FAZ D — Kling O3 timecoded multi-shot repair; 8 v03 prompts generated from revised clip manifests (long-hold splits, bracelet standalone insert, official snapshot)
- 2026-06-13 — SC0014 FAZ D — director's continuity pass; 8 O3 prompts revised to v02 (roster fixes, CLIP08 dolly-back fix, bracelet beat, infant-safety language)
- 2026-06-12 — SC0014 FAZ C â€” 8-clip plan + SCL ledger + 8 Format A O3 prompts (Kling ready)
- 2026-06-12 — lock PROP001 bracelet three-view + promote @PROP001_BRACELET to created (SC0014, QC>=85); SC0014 all elements created
- 2026-06-12 — lock LOC001 nursery three-view + promote @LOC001_NURSERY to created (SC0014, QC>=85)
<!-- AUTO:SESSION_LOG:END -->
