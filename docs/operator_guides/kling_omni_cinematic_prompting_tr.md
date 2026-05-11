# Kling Omni Sinematik Promptlama Rehberi (Repo-Uyumlu)

## 1. Kapsam ve doğrulama seviyesi

Bu rehber, uzun metraj üretim hedefini tek ve kontrolsüz bir prompt yerine şu zincire böler:

`scene -> clip -> shot -> element -> prompt variant -> QC`

Bu doküman operatör rehberidir; runtime API çağrısı içermez. Repo metadata-only ilkesine bağlıdır.

## 2. Omni 3 temel gerçekler

- Shot odaklı kurgu: bir shot = bir ana aksiyon.
- Süre aralığı: clip toplamı 3–15 saniye bandında tutulur.
- Native Audio ayrı pass olarak ele alınır; görsel kaliteyle karıştırılmaz.

## 3. Repo-uyumlu çalışma metodu

Aşağıdaki eşleme zorunludur:

- `preprod/` yerine: `source/` + `planning/`
- `elements/` yerine: `visual_dev/elements/` + `visual_dev/omni_sets/`
- `prompts/` yerine: `prompts/draft/`, `prompts/review/`, `prompts/approved/`, `prompts/locked/`
- `renders/` yerine: `evidence/prompt_runs/` + external storage refs
- `qc/` yerine: `evidence/omni_qc/` (veya `evidence/take_reviews/`)

Binary klasorleri (`renders/tests`, `renders/finals`) repo icinde acilmaz.

## 4. Cinematic prompt architecture

Temel ilke:

- Her clip bir `omni_clip_manifest` ile tanimlanir.
- `shots[]` icinde kamera/isik/motion alanlari acik ve denetlenebilir olur.
- `required_element_ids` -> `element_bindings` -> `@Alias` zinciri korunur.

## 5. Master cinematic template (repo dilinde)

Bir prompt metni asagidaki bilesenlerden render edilir:

1. Goal
2. Duration format
3. Scene context
4. Active elements
5. Shot plan
6. Action timeline
7. Camera grammar
8. Audio plan
9. Negative constraints
10. Style/color
11. Expected outcome
12. Retry rule

## 6. Cinematic Prompter notu

Prompt uretimi serbest metin yazimi degildir. Sistematik bilesen sirasi korunur.

- Safe: konservatif kurgu
- Creative: kontrollu atmosfer zenginlestirme
- Aggressive: daha sinematik ama kaynak-disina cikmayan kurgu

## 7. Varyant ve pass mantigi

Render pass ayrimi:

- `visual_test`: audio kapali varsayilan, kamera/kimlik/sureklilik odagi
- `performance_test`: audio sadece hazir speaker binding ile
- `final_candidate`: onceki pass notlariyla secilen aday
- `final_locked`: insan PR onayi ile kilitlenen secim

## 8. Sorun giderme matrisi (ozet)

Tipik sorunlar ve bir-sonraki denemede tek degisken kurali:

- Kimlik drift -> element alias ve constraints guclendir
- Kamera ziplamasi -> hareket yogunlugunu azalt
- Isik tutarsizligi -> lighting source/quality daha net yaz
- Isenmeyen konusma -> audio off / kisitli diyalog

Her retry tek bir degisken degistirir.

## 9. Hizli calisma recetesi

1. Scene beat plani netle.
2. Clip manifest olustur (`3–15s`).
3. Safe/Creative/Aggressive draft promptlarini uret.
4. Visual test gecmeden performance pass'a gecme.
5. QC kaydiyla retry rule yaz.
6. Final secimi insan PR review ile kilitle.

## 10. Kisa brief formu

- Scene ID:
- Clip ID:
- Ana aksiyon:
- Zorunlu elementler:
- Kamera niyeti:
- Isik niyeti:
- Audio gereksinimi:
- Risk (drift/artifact):
- Bir sonraki pass hedefi:

## 11. Uzun metraj pipeline notu

Uzun metrajda olceklenebilirlik birimleri:

- Scene bazli planlama
- Clip bazli prompt paketleri
- Shot bazli QC geri beslemesi

Bunun disina cikan tek-prompt yaklasimi kalite ve denetlenebilirlik kaybi yaratir.

## 12. Resmi dokuman / saha-pratik ayrimi

- Resmi model limitleri ve kurallari: `docs/model_guides/kling_omni.yaml`
- Saha-pratik ipuclari: deneyseldir, mutlak kural degildir.

Forum veya topluluk bilgisini resmi kural gibi uygulamayin.

## 13. Storage ilkesi

Repo metadata-only kalir. Medya dosyalari dis depoda tutulur.

Referans tipleri:

- `external_storage_ref`
- `platform_asset_ref`
- `local://`
- `gdrive://`
- `kling://`

