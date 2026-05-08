"""
B3 tests: SC0001 element_bindings.yaml baseline bindings.

Covers:
- C01 (Nadia): character, planned, blocked readiness
- C03 (Birta): character, planned, blocked readiness (correct per repo index, not C02)
- LOC001 (kitchen_passage): location_sub_area, planned, not_required readiness
- PROP003 (Vardova frame): prop, planned, not_required readiness
- All bindings have kling_native_audio.enabled == false (planned status, no Kling upload claim)
- No speaker_mapping (B5 owns dialogue_beats.yaml integration)
- Semantic validation via validate_element_binding()
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validators.validate_element_binding import (
    ElementBindingValidationError,
    validate_element_binding,
    validate_element_binding_batch,
)


@pytest.fixture
def sc0001_bindings() -> list[dict]:
    """Load SC0001 element_bindings.yaml and split YAML documents."""
    binding_file = REPO_ROOT / "visual_dev" / "omni_sets" / "SC0001" / "element_bindings.yaml"
    with binding_file.open(encoding="utf-8") as f:
        documents = list(yaml.safe_load_all(f))
    return documents


def test_c01_nadia_binding_valid(sc0001_bindings: list[dict]) -> None:
    """C01 (Nadia) binding must be valid: planned/none/blocked with kling_native_audio disabled."""
    c01 = sc0001_bindings[0]
    assert c01["element_id"] == "C01"
    assert c01["kling_alias"] == "@Nadia"
    assert c01["binding_status"] == "planned"
    assert c01["voice_capability"] == "none"
    assert c01["native_audio_readiness"] == "blocked"
    assert c01["kling_native_audio"]["enabled"] is False
    validate_element_binding(c01)  # Should not raise


def test_c03_birta_binding_valid(sc0001_bindings: list[dict]) -> None:
    """C03 (Birta) binding must be valid (C03 correct per repo character index, not C02)."""
    c03 = sc0001_bindings[1]
    assert c03["element_id"] == "C03"
    assert c03["kling_alias"] == "@Birta"
    assert c03["binding_status"] == "planned"
    assert c03["voice_capability"] == "none"
    assert c03["native_audio_readiness"] == "blocked"
    assert c03["kling_native_audio"]["enabled"] is False
    validate_element_binding(c03)  # Should not raise


def test_loc001_kitchen_passage_binding_valid(sc0001_bindings: list[dict]) -> None:
    """LOC001 (kitchen_passage) binding must be valid: location_sub_area, planned, not_required readiness."""
    loc001 = sc0001_bindings[2]
    assert loc001["element_id"] == "LOC001"
    assert loc001["element_type"] == "location_sub_area"
    assert loc001["kling_alias"] == "@ValeResidenceKitchenPassage"
    assert loc001["binding_status"] == "planned"
    assert loc001["voice_capability"] == "none"
    assert loc001["native_audio_readiness"] == "not_required"
    assert loc001["kling_native_audio"]["enabled"] is False
    validate_element_binding(loc001)  # Should not raise


def test_prop003_vardova_frame_binding_valid(sc0001_bindings: list[dict]) -> None:
    """PROP003 (Vardova frame) binding must be valid: prop, planned, not_required readiness."""
    prop003 = sc0001_bindings[3]
    assert prop003["element_id"] == "PROP003"
    assert prop003["element_type"] == "prop"
    assert prop003["kling_alias"] == "@VardovaFrame"
    assert prop003["binding_status"] == "planned"
    assert prop003["voice_capability"] == "none"
    assert prop003["native_audio_readiness"] == "not_required"
    assert prop003["kling_native_audio"]["enabled"] is False
    validate_element_binding(prop003)  # Should not raise


def test_all_bindings_have_kling_native_audio_disabled(sc0001_bindings: list[dict]) -> None:
    """All SC0001 bindings must have kling_native_audio.enabled == false (planned status baseline)."""
    for binding in sc0001_bindings:
        assert binding["kling_native_audio"]["enabled"] is False, (
            f"Binding {binding['element_id']} must have kling_native_audio.enabled=false "
            "(planned status implies no Kling upload claim yet)"
        )


def test_no_speaker_mapping_yet(sc0001_bindings: list[dict]) -> None:
    """No speaker_mapping should be present; B5 owns dialogue_beats.yaml integration."""
    for binding in sc0001_bindings:
        assert "speaker_mapping" not in binding or binding.get("speaker_mapping") is None, (
            f"Binding {binding['element_id']} should not have speaker_mapping yet; "
            "B5 (dialogue_beats.yaml) owns speaker mapping integration"
        )


def test_batch_validation_all_four_bindings_pass(sc0001_bindings: list[dict]) -> None:
    """Batch validation must pass all four SC0001 bindings without errors."""
    errors = validate_element_binding_batch(sc0001_bindings)
    assert errors == [], (
        f"Batch validation failed with {len(errors)} error(s): "
        + "; ".join(str(e) for e in errors)
    )
