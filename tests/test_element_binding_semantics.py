"""
A2.1 tests: element_binding semantic validation (cross-field rules).

Covers:
- binding_status == voice_capable requires voice_capability != none
- binding_status == voice_locked requires native_audio_readiness == ready
- binding_status == voice_locked requires voice_capability != none
- kling_native_audio.external_tts_allowed == false
- kling_native_audio.adr_vendor_allowed == false
- speaker_mapping dialogue_required + native_audio_readiness consistency
- native_audio_readiness == ready requires kling_native_audio.enabled == true for voice-capable
- planned bindings must not have kling_native_audio.enabled == true
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validators.validate_element_binding import (
    ElementBindingValidationError,
    validate_element_binding,
    validate_element_binding_batch,
)


def _minimal_binding(overrides: dict | None = None) -> dict:
    base = {
        "schema_version": "0.x-draft",
        "record_type": "element_binding",
        "element_id": "C01",
        "element_type": "character",
        "kling_alias": "@Nadia",
        "binding_status": "planned",
        "voice_capability": "none",
        "native_audio_readiness": "not_required",
        "kling_native_audio": {
            "enabled": False,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
        "provenance": {
            "created_by": "hknbb",
            "created_at": "2026-05-08T00:00:00Z",
        },
    }
    if overrides:
        base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Valid record tests
# ---------------------------------------------------------------------------


def test_valid_planned_non_voice_binding() -> None:
    record = _minimal_binding()
    validate_element_binding(record)  # Should not raise


def test_valid_created_non_voice_binding() -> None:
    record = _minimal_binding({
        "binding_status": "created",
        "voice_capability": "none",
        "native_audio_readiness": "not_required",
    })
    validate_element_binding(record)


def test_valid_voice_capable_with_audio_ref() -> None:
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "audio_ref",
        "native_audio_readiness": "metadata_only",
    })
    validate_element_binding(record)


def test_valid_voice_capable_with_library_provided() -> None:
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "library_provided",
        "native_audio_readiness": "metadata_only",
    })
    validate_element_binding(record)


def test_valid_voice_locked_with_library_provided_ready() -> None:
    record = _minimal_binding({
        "binding_status": "voice_locked",
        "voice_capability": "library_provided",
        "native_audio_readiness": "ready",
        "kling_native_audio": {
            "enabled": True,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
    })
    validate_element_binding(record)


def test_valid_with_speaker_mapping_dialogue_ready() -> None:
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "library_provided",
        "native_audio_readiness": "ready",
        "kling_native_audio": {
            "enabled": True,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
        "speaker_mapping": [
            {
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Nadia",
                "dialogue_required": True,
                "native_audio_readiness": "ready",
            }
        ],
    })
    validate_element_binding(record)


def test_valid_with_speaker_mapping_no_dialogue() -> None:
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "library_provided",
        "native_audio_readiness": "metadata_only",
        "speaker_mapping": [
            {
                "speaker_element_id": "C02",
                "speaker_kling_alias": "@Birta",
                "dialogue_required": False,
                "native_audio_readiness": "not_required",
            }
        ],
    })
    validate_element_binding(record)


# ---------------------------------------------------------------------------
# Invalid record tests - Rule violations
# ---------------------------------------------------------------------------


def test_voice_capable_with_voice_capability_none_fails() -> None:
    """Rule 1: binding_status == voice_capable requires voice_capability != none"""
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "none",
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 1" in str(exc_info.value)


def test_voice_locked_with_blocked_readiness_fails() -> None:
    """Rule 2: binding_status == voice_locked requires native_audio_readiness == ready"""
    record = _minimal_binding({
        "binding_status": "voice_locked",
        "voice_capability": "library_provided",
        "native_audio_readiness": "blocked",
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 2" in str(exc_info.value)


def test_voice_locked_with_metadata_only_readiness_fails() -> None:
    """Rule 2 continued: blocked and metadata_only both violate"""
    record = _minimal_binding({
        "binding_status": "voice_locked",
        "voice_capability": "library_provided",
        "native_audio_readiness": "metadata_only",
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 2" in str(exc_info.value)


def test_voice_locked_with_voice_capability_none_fails() -> None:
    """Rule 3: binding_status == voice_locked requires voice_capability != none"""
    record = _minimal_binding({
        "binding_status": "voice_locked",
        "voice_capability": "none",
        "native_audio_readiness": "ready",
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 3" in str(exc_info.value)


def test_external_tts_allowed_true_fails() -> None:
    """Rule 4: kling_native_audio.external_tts_allowed must be false"""
    record = _minimal_binding({
        "kling_native_audio": {
            "enabled": False,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": True,  # VIOLATION
            "adr_vendor_allowed": False,
        }
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 4" in str(exc_info.value)


def test_adr_vendor_allowed_true_fails() -> None:
    """Rule 5: kling_native_audio.adr_vendor_allowed must be false"""
    record = _minimal_binding({
        "kling_native_audio": {
            "enabled": False,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": True,  # VIOLATION
        }
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 5" in str(exc_info.value)


def test_speaker_mapping_dialogue_required_with_not_required_readiness_fails() -> None:
    """Rule 6: dialogue_required=true requires native_audio_readiness != not_required"""
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "library_provided",
        "native_audio_readiness": "ready",
        "speaker_mapping": [
            {
                "speaker_element_id": "C01",
                "speaker_kling_alias": "@Nadia",
                "dialogue_required": True,
                "native_audio_readiness": "not_required",  # VIOLATION
            }
        ],
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 6" in str(exc_info.value)


def test_voice_ready_without_enabled_fails() -> None:
    """Rule 7: native_audio_readiness=ready + voice_capability != none requires kling_native_audio.enabled=true"""
    record = _minimal_binding({
        "binding_status": "voice_capable",
        "voice_capability": "library_provided",
        "native_audio_readiness": "ready",
        "kling_native_audio": {
            "enabled": False,  # VIOLATION: should be true when native_audio_readiness=ready
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 7" in str(exc_info.value)


def test_planned_with_enabled_true_fails() -> None:
    """Rule 8: planned bindings must not have kling_native_audio.enabled=true"""
    record = _minimal_binding({
        "binding_status": "planned",
        "kling_native_audio": {
            "enabled": True,  # VIOLATION: planned implies asset doesn't exist yet
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
    })
    with pytest.raises(ElementBindingValidationError) as exc_info:
        validate_element_binding(record)
    assert "Rule 8" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Batch validation tests
# ---------------------------------------------------------------------------


def test_validate_batch_all_valid() -> None:
    records = [
        _minimal_binding(),
        _minimal_binding({"element_id": "C02", "kling_alias": "@Birta"}),
    ]
    errors = validate_element_binding_batch(records)
    assert errors == []


def test_validate_batch_with_errors() -> None:
    records = [
        _minimal_binding(),
        _minimal_binding({
            "element_id": "C02",
            "binding_status": "voice_capable",
            "voice_capability": "none",  # VIOLATION
        }),
    ]
    errors = validate_element_binding_batch(records)
    assert len(errors) == 1
    assert errors[0].record_id == "C02"
    assert "Rule 1" in errors[0].rule


def test_validate_batch_multiple_errors() -> None:
    records = [
        _minimal_binding({
            "element_id": "C01",
            "binding_status": "voice_capable",
            "voice_capability": "none",  # VIOLATION - Rule 1
        }),
        _minimal_binding({
            "element_id": "C02",
            "binding_status": "voice_locked",
            "voice_capability": "library_provided",
            "native_audio_readiness": "blocked",  # VIOLATION - Rule 2
        }),
    ]
    errors = validate_element_binding_batch(records)
    assert len(errors) == 2
    assert errors[0].record_id == "C01"
    assert errors[1].record_id == "C02"
