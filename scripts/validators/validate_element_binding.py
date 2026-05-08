"""
Semantic validation for element_binding records.

JSON Schema (element_binding.schema.json) validates structure and const fields.
This module enforces cross-field semantic rules that JSON Schema cannot express:
- binding_status and voice_capability relationships
- binding_status and native_audio_readiness relationships
- speaker_mapping dialogue_required and native_audio_readiness consistency
- kling_native_audio enforcement (no TTS, no ADR vendor)

Raises ElementBindingValidationError on violation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ElementBindingValidationError(ValueError):
    """Raised when an element_binding record violates semantic rules."""

    record_id: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.record_id}: {self.rule} — {self.message}"


def validate_element_binding(record: dict[str, Any]) -> None:
    """
    Validate semantic rules for an element_binding record.

    Rules enforced:
    1. binding_status == voice_capable requires voice_capability != none
    2. binding_status == voice_locked requires native_audio_readiness == ready
    3. binding_status == voice_locked requires voice_capability != none
    4. kling_native_audio.external_tts_allowed must be false
    5. kling_native_audio.adr_vendor_allowed must be false
    6. If speaker_mapping[].dialogue_required is true,
       speaker_mapping[].native_audio_readiness must not be not_required
    7. If top-level native_audio_readiness is ready,
       kling_native_audio.enabled should be true for voice-capable bindings
    8. planned bindings must not have kling_native_audio.enabled == true
       (planned status implies Kling asset does not yet exist)

    Args:
        record: element_binding dict with schema_version, record_type, etc.

    Raises:
        ElementBindingValidationError: if any rule is violated.
    """
    record_id = record.get("element_id", "unknown")
    binding_status = record.get("binding_status")
    voice_capability = record.get("voice_capability")
    native_audio_readiness = record.get("native_audio_readiness")
    kling_native_audio = record.get("kling_native_audio", {})
    speaker_mapping = record.get("speaker_mapping", [])

    # Rule 1: binding_status == voice_capable requires voice_capability != none
    if binding_status == "voice_capable" and voice_capability == "none":
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 1",
            message="binding_status=voice_capable requires voice_capability != none (got none)",
        )

    # Rule 2: binding_status == voice_locked requires native_audio_readiness == ready
    if binding_status == "voice_locked" and native_audio_readiness != "ready":
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 2",
            message=f"binding_status=voice_locked requires native_audio_readiness=ready (got {native_audio_readiness})",
        )

    # Rule 3: binding_status == voice_locked requires voice_capability != none
    if binding_status == "voice_locked" and voice_capability == "none":
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 3",
            message="binding_status=voice_locked requires voice_capability != none (got none)",
        )

    # Rule 4: kling_native_audio.external_tts_allowed must be false
    if kling_native_audio.get("external_tts_allowed") is not False:
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 4",
            message=f"kling_native_audio.external_tts_allowed must be false (got {kling_native_audio.get('external_tts_allowed')})",
        )

    # Rule 5: kling_native_audio.adr_vendor_allowed must be false
    if kling_native_audio.get("adr_vendor_allowed") is not False:
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 5",
            message=f"kling_native_audio.adr_vendor_allowed must be false (got {kling_native_audio.get('adr_vendor_allowed')})",
        )

    # Rule 6: speaker_mapping dialogue_required + native_audio_readiness consistency
    for i, speaker in enumerate(speaker_mapping):
        dialogue_required = speaker.get("dialogue_required", False)
        speaker_native_audio_readiness = speaker.get("native_audio_readiness")
        if dialogue_required and speaker_native_audio_readiness == "not_required":
            raise ElementBindingValidationError(
                record_id=record_id,
                rule="Rule 6",
                message=f"speaker_mapping[{i}]: dialogue_required=true requires native_audio_readiness != not_required (got not_required)",
            )

    # Rule 7: If top-level native_audio_readiness is ready,
    # kling_native_audio.enabled should be true for voice-capable bindings
    if (
        native_audio_readiness == "ready"
        and voice_capability != "none"
        and kling_native_audio.get("enabled") is not True
    ):
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 7",
            message="native_audio_readiness=ready with voice_capability != none requires kling_native_audio.enabled=true",
        )

    # Rule 8: planned bindings must not have kling_native_audio.enabled == true
    if binding_status == "planned" and kling_native_audio.get("enabled") is True:
        raise ElementBindingValidationError(
            record_id=record_id,
            rule="Rule 8",
            message="binding_status=planned implies Kling asset does not yet exist; kling_native_audio.enabled must be false",
        )


def validate_element_binding_batch(records: list[dict[str, Any]]) -> list[ElementBindingValidationError]:
    """
    Validate a batch of element_binding records.

    Args:
        records: list of element_binding dicts.

    Returns:
        List of ElementBindingValidationError for all records that fail.
        Empty list if all records pass.
    """
    errors = []
    for record in records:
        try:
            validate_element_binding(record)
        except ElementBindingValidationError as e:
            errors.append(e)
    return errors
