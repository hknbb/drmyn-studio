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
- 2026-06-15 — SC0014 Anchor & Animate pipeline Faz 0â€“6 (shot-photography-first)
- 2026-06-12 — SC0014 FAZ C â€” 8-clip plan + SCL ledger + 8 Format A O3 prompts (Kling ready)
- 2026-06-12 — lock PROP001 bracelet three-view + promote @PROP001_BRACELET to created (SC0014, QC>=85); SC0014 all elements created
- 2026-06-12 — lock LOC001 nursery three-view + promote @LOC001_NURSERY to created (SC0014, QC>=85)
- 2026-06-12 — complete C02 Roman full pipeline + promote @C02_ROMAN to created (SC0111, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-3 four-view + promote @C09_OTTO to created (SC0047, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-2 oref (ott_2.png) + update identity anchor
- 2026-06-10 — update C09 Otto wardrobe to dark navy/blue + muted olive-green (WD014)
- 2026-06-10 — add C09 Otto Stage-2 --oref lock prompt with CDN URL
- 2026-06-10 — lock C09 Otto Stage-1 hero (MJ_C09_HERO_V001)
<!-- AUTO:SESSION_LOG:END -->
