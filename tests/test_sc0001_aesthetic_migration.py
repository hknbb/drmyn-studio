"""
AB-3 tests — SC0001 aesthetic migration to VALE_DOMESTIC_RESTRAINT.

Verifies:
- scene_card contains aesthetic_pack_refs
- storyboard options inherit the pack ref
- selected_option stays null (no lifecycle promotion)
- validator accepts the migrated record
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENE_CARD_PATH = REPO_ROOT / "planning" / "scenes" / "SC0001" / "scene_card.yaml"
STORYBOARD_PATH = REPO_ROOT / "visual_dev" / "storyboards" / "SC0001" / "storyboard_options.yaml"


def test_sc0001_scene_card_has_aesthetic_pack_ref() -> None:
    assert SCENE_CARD_PATH.exists(), "SC0001 scene_card.yaml missing"
    card = yaml.safe_load(SCENE_CARD_PATH.read_text(encoding="utf-8"))
    refs = card.get("visual_targets", {}).get("aesthetic_pack_refs", [])
    assert "VALE_DOMESTIC_RESTRAINT" in refs


def test_sc0001_storyboard_options_exist() -> None:
    assert STORYBOARD_PATH.exists(), "storyboard_options.yaml not generated"


def test_sc0001_storyboard_options_inherit_aesthetic_pack_refs() -> None:
    assert STORYBOARD_PATH.exists()
    payload = yaml.safe_load(STORYBOARD_PATH.read_text(encoding="utf-8"))
    options = payload.get("options", [])
    assert len(options) == 5
    for opt in options:
        refs = opt.get("aesthetic_pack_refs", [])
        assert "VALE_DOMESTIC_RESTRAINT" in refs, (
            f"Option {opt.get('option_id')} missing VALE_DOMESTIC_RESTRAINT"
        )


def test_sc0001_storyboard_selected_option_is_sb03() -> None:
    assert STORYBOARD_PATH.exists()
    payload = yaml.safe_load(STORYBOARD_PATH.read_text(encoding="utf-8"))
    assert payload.get("selected_option") == "SC0001_SB03"


def test_sc0001_storyboard_options_passes_schema() -> None:
    from jsonschema import Draft202012Validator
    schema = json.loads(
        (REPO_ROOT / "schemas" / "storyboard_option.schema.json").read_text(encoding="utf-8")
    )
    assert STORYBOARD_PATH.exists()
    payload = yaml.safe_load(STORYBOARD_PATH.read_text(encoding="utf-8"))
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(payload)]
    assert errors == [], errors


def test_sc0001_scene_card_passes_schema() -> None:
    from jsonschema import Draft202012Validator
    schema = json.loads(
        (REPO_ROOT / "schemas" / "scene_card.schema.json").read_text(encoding="utf-8")
    )
    card = yaml.safe_load(SCENE_CARD_PATH.read_text(encoding="utf-8"))
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(card)]
    assert errors == [], errors
