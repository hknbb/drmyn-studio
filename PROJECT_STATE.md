# PROJECT_STATE.md — Living Status Dashboard

> Read this first in every session. Update it after every promotion, lock,
> stage completion, or significant decision (see Update Contract in `AGENTS.md`).

## 🇹🇷 Şu An Neredeyiz (Türkçe Özet)

Milestone M5'teyiz: ana karakterlerin görsel element pipeline'ı (MJ hero →
--oref lock → four-view → binding "created"). Son iş (12 Haziran): C02 Roman'ın
tam pipeline'ı tamamlandı ve SC0111 binding'i "created" seviyesine yükseltildi.
C01, C02, C04, C06, C08, C09 ve C10 (Carrier+Holder) karakterlerinin binding'leri
"created" durumda. Sırada: C03 Birta ve C05 Marcus'un üretilmiş görsellerinin
kayıt altına alınması (PR-BATCH-KEYCHAR-1 batch PR'ı), ardından C07 Sera ve
Halo Unit, sonra golden scene üretimi (aktif branch SC0014 sahne üretimi için
açıldı). Bilinen yapısal sorunlar aşağıda "Known Issues" bölümünde.

## Status

| Field | Value |
|---|---|
| Active branch | `feat/sc0014-scene-production` |
| Milestone | M5 — character visual element pipeline |
| Last updated | 2026-06-12 |
| Public checkpoint | v0.17.0 (Zenodo DOI: 10.5281/zenodo.20241807) |

## Character Pipeline (C01–C10)

Stages: S1 = MJ v8.1 hero · S2 = MJ v7 --oref identity lock · S3 = four-view pack · Binding = lifecycle status

| ID | Name | S1 | S2 | S3 | Binding | Scene(s) | Notes |
|---|---|---|---|---|---|---|---|
| C01 | Nadia Vale | ✅ | ✅ | ✅ | **created** | SC0047, SC0089, SC0111 | 4 look bindings created: base, field-night, transit, battle-worn (+nursery four-view) |
| C02 | Roman Vale | ✅ | ✅ | ✅ | **created** | SC0111 | Full pipeline completed 2026-06-12, QC≥85 |
| C03 | Birta | — | — | — | pending registration | — | Visuals produced in-session (pre-checkpoint); needs PR-BATCH-KEYCHAR-1 registration |
| C04 | Dimitri | ✅ | ✅ | ✅ | **created** | SC0014 | Dual-seed four-view pack, QC≥85 |
| C05 | Marcus | — | — | — | pending registration | — | Visuals produced in-session (pre-checkpoint); needs PR-BATCH-KEYCHAR-1 registration |
| C06 | Zara | ✅ | ✅ | ✅ | **created** | SC0089 | Khaki/olive-tan wardrobe WD013, QC≥85 |
| C07 | Sera | — | — | — | not started | — | Queued after key-character batch |
| C08 | Jin | ✅ | ✅ | ✅ | **created** | SC0014 | Protected subject, QC≥85 |
| C09 | Otto | ✅ | ✅ | ✅ | **created** | SC0047 | Dark navy/olive wardrobe WD014, QC≥85 |
| C10 | Carrier+Holder | ✅ | ✅ | ✅ | **created** | SC0014 | Two distinct enforcer figures, per-figure packs, QC≥85 |

## Active Scene Work

- Branch opened for **SC0014** scene production; character bindings for SC0014
  (C04, C08, C10) are created — scene-level work not yet started.
- Golden scenes referenced by created bindings: **SC0014, SC0047, SC0089, SC0111**.
- Golden scene **SC0001** queued in the revised plan (after character batch).

## Next Steps (priority order)

1. **PR-BATCH-KEYCHAR-1** — register the pre-checkpoint visual batch
   (originally C02–C05; C02 now done in-repo → effectively **C03 Birta + C05
   Marcus**): reference_chain, perspective packs, image selections, QC records,
   media index, kling element refs. See `revised_character_batch_to_golden_scene_plan.md`.
2. **C07 Sera** + **Halo Unit** element production (same 3-stage pipeline).
3. **Golden scene production** — SC0014 (active branch) / SC0001 per revised plan.
4. Refresh `revised_character_batch_to_golden_scene_plan.md` — it predates the
   C02/C06/C08/C09/C10 completions recorded above.

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

- 2026-06-12 — Cross-CLI memory system installed (AGENTS.md contract + this dashboard); home-dir CLAUDE.md conflict removed.
- 2026-06-12 — C02 Roman full pipeline (S1 hero → S2 oref → S3 four-view) + promoted to created (SC0111, QC≥85).
- 2026-06-10 — C09 Otto full pipeline + created (SC0047, WD014); C10 Carrier+Holder four-views + created (SC0014).
- 2026-06-10 — C06 Zara full pipeline + created (SC0089, WD013 khaki).
- 2026-06-09 — C01 battle-worn + transit four-views; C04 operational four-view; C08 nursery four-view → bindings created.
- 2026-06-08 — C01 field-night + nursery four-views.
