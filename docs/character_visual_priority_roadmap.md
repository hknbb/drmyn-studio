# Character Visual Priority Roadmap

**Status:** Active, applies after PR-BATCH-KEYCHAR-1 (key-character v2 visual batch).
**Source plan:** `revised_character_batch_to_golden_scene_plan.md` § Phase 1.
**Purpose:** Sabit visual production sırasını ve compact-planning ↔ source-truth ID e?lemesini dokumante etmek. Golden scene öncesi karar belirsizligi yaratmamak için.

---

## Critical ID Discipline Invariant

```text
All visual production records use compact planning IDs.
Source-truth IDs remain only inside source_truth_reference fields and documentation.
Do not create duplicate characters when source ID and compact planning ID differ.
Do not reuse a compact slot already taken (e.g., compact C04 = Dimitri, never reuse for Zara).
```

Compact slot C01–C05 zaten dolu. Yeni intake'ler **sıradaki bo? compact ID** alır (C06, C07, C08, ...) — source-truth ID ile aynı sayı denk gelse bile bu raslantıdır, kural ihlali degildir.

---

## Production Roster

```text
Compact ID  Source ID  Name                    Role                                       Action
==========  =========  ======================  =========================================  ======================================
C01         C01        Nadia Vale              protagonist                                clean v2 rebuild (Phase 2)
C02         C02        Roman Vale              primary antagonist / system architect      v2 closed in PR-BATCH-KEYCHAR-1; audit only
C03         C23        Birta                   domestic/supporting anchor                 v2 closed in PR-BATCH-KEYCHAR-1; scene-specific use later
C04         C06        Dimitri Koss            operational antagonist support             v2 closed in PR-BATCH-KEYCHAR-1; audit only
C05         C03        Marcus Chen             catalyst / ghost                           v2 closed in PR-BATCH-KEYCHAR-1; audit only

HERALD_HALO C05        The Herald / Halo Unit  system antagonist / broadcast presence     character-like system element (Phase 3, additive schema)
C06         C04        Zara Okonkwo            primary ally / emotional B-story           source intake + visual scaffold (Phase 4)
C07         C07        Sera (Seraphina Mast)   media ally / publication arc               source intake + visual scaffold (Phase 7)
C08         C12        Jin Vale                emotional objective (protected subject)    protected-subject visual scaffold (Phase 6)
```

**ID collision note:** Compact C04 = Dimitri, source-truth C04 = Zara. Zara compact ID alarak C06 olur; source kayıt `source_truth_reference.source_character_id: C04` olarak saklanır. Aynı düzen Marcus için de geçerli (compact C05, source-truth C03).

---

## Production Order (after PR-BATCH-KEYCHAR-1 merge)

```text
1.  PR-CHAR-0          docs(characters): visual priority roadmap        ← THIS PR
2.  PR-C01-1           chore(c01): scaffold clean Nadia v2 reference chain
3.  PR-C01-2           chore(c01): register clean Nadia v2 visual references
4.  PR-HALO-1          schema(elements): scaffold Herald Halo Unit as character-like system element
5.  PR-HALO-2          chore(herald): register Halo Unit visual identity references
6.  PR-ZARA-1          chore(characters): add Zara source-truth visual scaffold
7.  PR-ZARA-2          chore(zara): register Zara v2 visual references
8.  PR-DIMITRI-1       chore(c04): finalize Dimitri visual readiness records  (audit-only follow-up if needed)
9.  PR-JIN-1           chore(characters): add Jin Vale protected-subject visual scaffold
10. PR-JIN-2           chore(jin): register Jin Vale protected-subject visual references
11. PR-SERA-1          chore(characters): add Sera visual planning scaffold
12. PR-SERA-2          chore(sera): register Sera v2 visual references
13. PR-GOLDEN-0        docs(golden): evaluate candidate scenes for full reference production
14. PR-GOLDEN-1..7     feat(golden): full golden scene production
15. tag                v0.18.0-golden-reference-scene
```

---

## Phase-Specific Per-Character Notes

### C01 Nadia — clean v2 rebuild (additive)

Mevcut C01 v1 kayıtları (`character_identity_anchor.yaml`, `image_selection.yaml`, `kling_element_reference.yaml` v1, `pack_manifest.yaml`, `identity_evidence_sets/`, v1 `look_variants/`, v1 `gpt_images_perspective_pack.yaml` ile `three_view_no_rear`) **dokunulmaz** — SC0001 TAKE002 chain'i korunur. Yeni v2 chain ayrı path altında izole edilir:

```text
visual_dev/elements/characters/C01/look_variants/C01_NADIA_CANON_V2/reference_chain.yaml
visual_dev/elements/characters/C01/look_variants/C01_NADIA_CANON_V2/gpt_images_perspective_pack.yaml
```

@Nadia alias migration **ayrı PR** ile, sonra yapılır.

### HERALD_HALO — character-like system element

Halo Unit prop degil, **system embodiment**. Mevcut `element_type` enum'unda (`character/location/prop/wardrobe/style/other`) yok → additive schema:

```text
schemas/system_character_element.schema.json                 [new]
schemas/system_character_reference_chain.schema.json         [new]
scripts/validate_production_records.py                       [register both]
visual_dev/elements/system_characters/HERALD_HALO/...        [new]
```

**Üretim akı?ı:** MJ Stage 1/2 atlanır (robotik gövde için kimlik anchor'a gerek yok), GPT Images 2 direct path.

### Zara (C06), Jin (C08), Sera (C07) — yeni intake

Her biri için **iki adım**:
1. Planning record + visual scaffold (PR-X-1): `planning/characters/C0N.yaml`, `visual_dev/elements/characters/C0N/{reference_chain,gpt_images_perspective_pack}.yaml`
2. Visual üretim (PR-X-2): MJ Stage 1 → Stage 2 → GPT Images 2 → QC → Kling ref

Jin için: protected-subject prompt/QC ilkeleri (infant safety, no distress exploitation, no action posing).
Sera için: dossier'da `visual_profile` yok — Phase 7'de draft önerilir, kullanıcı onayından sonra yazılır.

### Dimitri (C04) audit

C04 v2 zaten PR-BATCH-KEYCHAR-1'de kapandı. PR-DIMITRI-1 sadece readiness audit veya kapatılmamı? deferred item kaldıysa cleanup. Eger her ?ey temizse bu PR atlanır.

---

## Out of Scope

Bu roadmap **production sırasını** sabitler. ?u kararlar **dı?ında**:

```text
native_audio_readiness promotion       (sahne üretiminde, dialogue ready oldugunda)
Kling video generation                 (Phase 9 golden scene)
golden scene seçimi                    (PR-GOLDEN-0, karakter readiness sonrası)
public release / Zenodo                (sadece methodology/schema/full scene tamamlaninca)
SC0001 / TAKE002 chain mutation        (kesinlikle hayır — koru)
```

---

## Validation per follow-up PR

Tüm sıradaki PR'lar a?agıdaki kontrolü geçmelidir:

```bash
python scripts/validate_production_records.py --repo-root .
python -m pytest -q
```

Scene readiness'i etkileyen i?lerde ek:

```bash
python scripts/agents/scene_readiness.py --scene <SCENE_ID>
```

PR açıklamasında sayılar verilir.

---

## Related Documents

- `revised_character_batch_to_golden_scene_plan.md` — full revised roadmap (root)
- `final_revize_production_roadmap.md` — earlier roadmap draft (root)
- `docs/methodology/` — methodology references
- `templates/element_reference_prompts/character_mj_v8_narrative_identity.md` — Stage 1 MJ V8.1 template
- `templates/element_reference_prompts/character_mj_v7_oref_refinement.md` — Stage 2 MJ V7 oref template
