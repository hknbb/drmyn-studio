# Omni Prompt Component Model

Bu dokuman Kling Omni prompt metninin tek parca serbest metin yerine
bilesenlerden derlenmesini tanimlar.

## Canonical component order

1. `goal`
2. `duration_format`
3. `scene_context`
4. `active_elements`
5. `shot_plan`
6. `action_timeline`
7. `camera_grammar`
8. `audio_plan`
9. `negative_constraints`
10. `style_color`
11. `expected_outcome`
12. `retry_rule`

## Component -> source mapping

- `goal` -> `planning/scenes/SC####/scene_card.yaml` (`purpose`) + beat role
- `duration_format` -> `planning/scenes/SC####/manifests/*_manifest.yaml` (`total_duration_seconds`)
- `scene_context` -> `scene_card` + `planning/locations/*.yaml`
- `active_elements` -> `visual_dev/omni_sets/SC####/element_bindings.yaml` + `required_element_ids`
- `shot_plan` -> `omni_clip_manifest.shots[]`
- `action_timeline` -> `shots[].duration_seconds` + `shots[].prompt_action`
- `camera_grammar` -> `shots[].camera`
- `audio_plan` -> `kling_native_audio` + `planning/scenes/SC####/dialogue_beats.yaml`
- `negative_constraints` -> model guide defaults + prompt record negative constraints
- `style_color` -> `planning/aesthetic_bible.yaml` + shot lighting
- `expected_outcome` -> `prompt_record.expected_output`
- `retry_rule` -> QC kaydi veya sonraki pass notu

## Rendering rule

Adapter, `prompt_text` alanini bu siradaki bilesenlerden olusturur.
Bilesenlerin yeri rastgele degismez.

## Policy constraints

- Canonical planning ID'leri prompt metnine sizmaz.
- `required_element_aliases` korunur ve prompt'ta gorunur.
- Prompt char limiti asilirsa hard guard uygulanir.
- Yeni story fact uydurulmaz.

## Variant compatibility

Model, varyant politikasiyla uyumludur:

- `safe`
- `creative`
- `aggressive`

Her varyant ayni component iskeletini kullanir; yalniz ifade yogunlugu degisir.
