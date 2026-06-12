# PROJECT_STATE.md — Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## 🇹🇷 Şu An Neredeyiz (Türkçe Özet)

Milestone M5'teyiz: SC0014 lokasyon elementleri üretimi süruyor.
LOC001 Vale nursery tam pipeline tamamlandı ve "created" seviyesine yükseltildi
(first-ref loc001_1.png → 3-view QC 91/88/90 → KER_LOC001_NURSERY_V001 →
@LOC001_NURSERY binding created). Sırada: PROP001 pale-blue bracelet (SC0014'ün
son pending elementi). Bilinen yapısal sorunlar "Known Issues" bölümünde.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 — character visual element pipeline |
| Last updated | 2026-06-12 |
| Public checkpoint | v0.17.0 (Zenodo DOI: 10.5281/zenodo.20241807) |

## Character Pipeline (C01–C10)

<!-- AUTO:PIPELINE:START -->
Stages: S1 = MJ v8.1 hero · S2 = MJ v7 --oref identity lock · S3 = four-view pack · Binding = lifecycle status

| ID | Name | S1 | S2 | S3 | Binding | Scene(s) | Notes |
|---|---|---|---|---|---|---|---|
| C01 | Nadia Vale | ✅ | ✅ | ✅ | **created** | SC0047, SC0089, SC0111 | 4 look bindings created: base, field-night, transit, battle-worn |
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

1. **LOC001 Vale nursery** (SC0014) — first-ref prompt created → user generates
   in ChatGPT Images → archive → PPACK 3-view source_reference_id updated →
   user generates 3 views → archive → PQC (≥85) → image_selection → KER →
   binding `planned → created`. (ACTIVE)
2. **PROP001 pale-blue bracelet** (SC0014) — same first-ref + scale-angle pipeline.
3. Remaining locations: SC0089 night transit, LOC006 Merin quay, LOC007 Veltain antechamber.
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
- 2026-06-12 — LOC001 Vale nursery full pipeline + promote @LOC001_NURSERY to created (SC0014, QC>=85)
- 2026-06-12 — complete C02 Roman full pipeline + promote @C02_ROMAN to created (SC0111, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-3 four-view + promote @C09_OTTO to created (SC0047, QC>=85)
- 2026-06-10 — lock C09 Otto Stage-2 oref (ott_2.png) + update identity anchor
- 2026-06-10 — update C09 Otto wardrobe to dark navy/blue + muted olive-green (WD014)
- 2026-06-10 — add C09 Otto Stage-2 --oref lock prompt with CDN URL
- 2026-06-10 — lock C09 Otto Stage-1 hero (MJ_C09_HERO_V001)
- 2026-06-10 — promote C06 Zara to created (SC0089, QC>=85, khaki WD013)
- 2026-06-10 — update C06 Zara wardrobe to khaki/olive-tan (WD013)
- 2026-06-10 — [chore] rename C06 archive paths to zar_1/zar_2 convention
- 2026-06-10 — lock C06 Zara Stage-2 --oref identity lock (MJ_C06_OREFLOCK_V001)
<!-- AUTO:SESSION_LOG:END -->
