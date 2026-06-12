# PROJECT_STATE.md — Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## 🇹🇷 Şu An Neredeyiz (Türkçe Özet)

Milestone M5'teyiz: SC0014 FAZ C tamamlandı — 8 clip, 8 O3 prompt (Format A, diyalog suppress),
continuity ledger SCL_SC0014_V001. SC0014 artık Kling üretimine hazır (FAZ D/E: kullanıcı video
üretir + takes seçer). Sıradaki öncelik: SC0089, SC0047, SC0111 sahne elementleri (lokasyon +
prop pipeline'ları). Bilinen yapısal sorunlar "Known Issues" bölümünde.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 — character visual element pipeline |
| Last updated | 2026-06-12 (FAZ C complete) |
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

- Branch opened for **SC0014** scene production; character bindings for SC0014
  (C04, C08, C10) are created — scene-level work not yet started.
- Golden scenes referenced by created bindings: **SC0014, SC0047, SC0089, SC0111**.
- Golden scene **SC0001** queued in the revised plan (after character batch).

## Next Steps (priority order)

1. **SC0014 FAZ D/E** — kullanıcı Kling O3'te 8 clip üretir → takes → selected_take → scene_clip_map. (operator-driven)
2. **SC0089, SC0047, SC0111 element pipeline** — remaining locations + props (first-ref → 3-view → KER → created). (NEXT metadata)
3. **PR-BATCH-KEYCHAR-1** — C03 Birta + C05 Marcus pre-checkpoint registration.
4. **C07 Sera** + **Halo Unit** element production.

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
- 2026-06-12 — SC0014 FAZ C complete: 8-clip plan + SCL_SC0014_V001 ledger + 8 Format A O3 prompts (dialogue suppressed; Kling ready)
- 2026-06-12 — lock PROP001 bracelet three-view + promote @PROP001_BRACELET to created (SC0014, QC>=85); SC0014 all elements created
- 2026-06-12 — lock LOC001 nursery three-view + promote @LOC001_NURSERY to created (SC0014, QC>=85)
- 2026-06-12 — complete C02 Roman full pipeline + promote @C02_ROMAN to created (SC0111, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-3 four-view + promote @C09_OTTO to created (SC0047, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-2 oref (ott_2.png) + update identity anchor
- 2026-06-10 — update C09 Otto wardrobe to dark navy/blue + muted olive-green (WD014)
- 2026-06-10 — add C09 Otto Stage-2 --oref lock prompt with CDN URL
- 2026-06-10 — lock C09 Otto Stage-1 hero (MJ_C09_HERO_V001)
- 2026-06-10 — promote C06 Zara to created (SC0089, QC>=85, khaki WD013)
- 2026-06-10 — update C06 Zara wardrobe to khaki/olive-tan (WD013)
<!-- AUTO:SESSION_LOG:END -->
