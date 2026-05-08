"""
Semantic validator for dialogue_beats records.

Enforces cross-reference rules that JSON Schema cannot express:
1. target_beat_id must exist in source_scene_beat_plan
2. speaker_element_id must exist in source_element_bindings
3. speaker_kling_alias must match the binding's kling_alias
4. line_id uniqueness within a single scene
5. native_audio_readiness: ready requires voice_capability != none in binding
6. dialogue_required: true with native_audio_readiness: blocked is allowed (readiness blocker)
7. No external TTS / ADR / ElevenLabs vendor fields
8. Referenced source files must exist
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DialogueBeatsValidationError(ValueError):
    """Raised when a dialogue_beats record violates semantic rules."""

    scene_id: str
    error_code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.scene_id}] {self.error_code}: {self.message}"


@dataclass
class DialogueBeatsReadinessBlocker:
    """Warning: dialogue line marked required but audio not ready. Not a validation failure."""

    scene_id: str
    line_id: str
    speaker_element_id: str
    message: str

    def __str__(self) -> str:
        return f"[{self.scene_id}] READINESS_BLOCKER {self.line_id}: {self.message}"


def _load_yaml_documents(file_path: str | Path) -> list[dict]:
    """Load all YAML documents from a file (multi-document YAML)."""
    path = Path(file_path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    return [d for d in docs if d is not None]


def _load_scene_beat_plan(repo_root: str | Path, ref: str) -> set[str]:
    """Load beat_ids from scene_beat_plan.yaml referenced by path."""
    full_path = Path(repo_root) / ref
    docs = _load_yaml_documents(full_path)
    beat_ids = set()
    for doc in docs:
        if isinstance(doc, dict):
            source_beats = doc.get("source_beats", [])
            for beat in source_beats:
                beat_id = beat.get("beat_id")
                if beat_id:
                    beat_ids.add(beat_id)
    return beat_ids


def _load_element_bindings(repo_root: str | Path, ref: str) -> dict[str, str]:
    """
    Load element_id -> kling_alias mapping from element_bindings.yaml.
    Returns dict: {element_id: kling_alias, ...}
    """
    full_path = Path(repo_root) / ref
    docs = _load_yaml_documents(full_path)
    bindings: dict[str, str] = {}
    binding_voice_capability: dict[str, str] = {}
    binding_status: dict[str, str] = {}

    for doc in docs:
        if isinstance(doc, dict):
            element_id = doc.get("element_id")
            kling_alias = doc.get("kling_alias")
            voice_cap = doc.get("voice_capability", "none")
            b_status = doc.get("binding_status", "planned")
            if element_id and kling_alias:
                bindings[element_id] = kling_alias
                binding_voice_capability[element_id] = voice_cap
                binding_status[element_id] = b_status

    # Return both mappings as a tuple so caller can access voice_capability too
    return bindings, binding_voice_capability, binding_status


def validate_dialogue_beats(
    record: dict[str, Any], repo_root: str | Path
) -> tuple[list[DialogueBeatsValidationError], list[DialogueBeatsReadinessBlocker]]:
    """
    Validate a single dialogue_beats record for semantic correctness.

    Rules enforced (hard failures):
    1. target_beat_id must exist in source_scene_beat_plan
    2. speaker_element_id must exist in source_element_bindings
    3. speaker_kling_alias must match binding's kling_alias
    4. line_id values must be unique within the dialogue_beats record
    5. native_audio_readiness: ready requires voice_capability != none
    6. No external TTS / ADR vendor fields (defensive check)
    7. Referenced source files must exist

    Readiness blockers (warnings, not failures):
    - dialogue_required: true with native_audio_readiness: blocked

    Args:
        record: dialogue_beats dict with schema_version, record_type, etc.
        repo_root: root directory of the repository

    Returns:
        Tuple of (errors, blockers) where errors are validation failures
        and blockers are readiness warnings.
    """
    errors: list[DialogueBeatsValidationError] = []
    blockers: list[DialogueBeatsReadinessBlocker] = []

    scene_id = record.get("scene_id", "UNKNOWN")
    repo_root_path = Path(repo_root)

    # Load references
    scene_beat_plan_ref = record.get("source_scene_beat_plan_ref")
    element_bindings_ref = record.get("source_element_bindings_ref")

    # Rule 7: Check referenced files exist
    if scene_beat_plan_ref:
        scene_beat_path = repo_root_path / scene_beat_plan_ref
        if not scene_beat_path.exists():
            errors.append(
                DialogueBeatsValidationError(
                    scene_id=scene_id,
                    error_code="MISSING_SCENE_BEAT_PLAN",
                    message=f"source_scene_beat_plan_ref points to missing file: {scene_beat_plan_ref}",
                )
            )
            # Can't proceed without beat plan reference
            return errors, blockers

    if element_bindings_ref:
        element_bindings_path = repo_root_path / element_bindings_ref
        if not element_bindings_path.exists():
            errors.append(
                DialogueBeatsValidationError(
                    scene_id=scene_id,
                    error_code="MISSING_ELEMENT_BINDINGS",
                    message=f"source_element_bindings_ref points to missing file: {element_bindings_ref}",
                )
            )
            # Can't proceed without element bindings reference
            return errors, blockers

    # Load beat IDs and element bindings
    beat_ids = _load_scene_beat_plan(repo_root, scene_beat_plan_ref) if scene_beat_plan_ref else set()
    (
        bindings,
        binding_voice_capability,
        binding_status,
    ) = _load_element_bindings(repo_root, element_bindings_ref) if element_bindings_ref else ({}, {}, {})

    dialogue_lines = record.get("dialogue_lines", [])

    # Rule 4: Check line_id uniqueness
    line_ids = [line.get("line_id") for line in dialogue_lines]
    seen_ids: set[str] = set()
    for line_id in line_ids:
        if line_id in seen_ids:
            errors.append(
                DialogueBeatsValidationError(
                    scene_id=scene_id,
                    error_code="DUPLICATE_LINE_ID",
                    message=f"line_id {line_id!r} appears multiple times; must be unique within scene",
                )
            )
        else:
            seen_ids.add(line_id)

    # Validate each dialogue line
    for idx, line in enumerate(dialogue_lines):
        line_id = line.get("line_id", f"[index {idx}]")
        target_beat_id = line.get("target_beat_id")
        speaker_element_id = line.get("speaker_element_id")
        speaker_kling_alias = line.get("speaker_kling_alias")
        native_audio_readiness = line.get("native_audio_readiness")
        dialogue_required = line.get("dialogue_required", False)

        # Rule 1: target_beat_id exists in scene_beat_plan
        if target_beat_id and beat_ids and target_beat_id not in beat_ids:
            errors.append(
                DialogueBeatsValidationError(
                    scene_id=scene_id,
                    error_code="MISSING_BEAT_ID",
                    message=f"line {line_id!r}: target_beat_id={target_beat_id!r} not found in {scene_beat_plan_ref}",
                )
            )

        # Rule 2: speaker_element_id exists in element_bindings
        if speaker_element_id and bindings and speaker_element_id not in bindings:
            errors.append(
                DialogueBeatsValidationError(
                    scene_id=scene_id,
                    error_code="MISSING_ELEMENT_ID",
                    message=f"line {line_id!r}: speaker_element_id={speaker_element_id!r} not found in {element_bindings_ref}",
                )
            )
            # Can't check alias if element not found
            continue

        # Rule 3: speaker_kling_alias matches binding
        if speaker_element_id and bindings and speaker_element_id in bindings:
            expected_alias = bindings[speaker_element_id]
            if speaker_kling_alias != expected_alias:
                errors.append(
                    DialogueBeatsValidationError(
                        scene_id=scene_id,
                        error_code="ALIAS_MISMATCH",
                        message=f"line {line_id!r}: speaker_kling_alias={speaker_kling_alias!r} does not match binding for {speaker_element_id} (expected {expected_alias!r})",
                    )
                )

            # Rule 5: native_audio_readiness: ready requires voice_capability != none
            if native_audio_readiness == "ready":
                voice_cap = binding_voice_capability.get(speaker_element_id, "none")
                if voice_cap == "none":
                    errors.append(
                        DialogueBeatsValidationError(
                            scene_id=scene_id,
                            error_code="UNWARRANTED_READINESS",
                            message=f"line {line_id!r}: native_audio_readiness=ready but {speaker_element_id} has voice_capability=none",
                        )
                    )

            # Readiness blocker: dialogue_required: true with blocked readiness
            if (
                dialogue_required
                and native_audio_readiness == "blocked"
            ):
                blockers.append(
                    DialogueBeatsReadinessBlocker(
                        scene_id=scene_id,
                        line_id=line_id,
                        speaker_element_id=speaker_element_id,
                        message=f"dialogue_required=true but native_audio_readiness=blocked ({speaker_element_id}); voice provisioning awaited",
                    )
                )

    # Rule 6: Defensive check for external TTS / ADR fields (schema should reject, but check anyway)
    kling_native_audio = record.get("kling_native_audio", {})
    if kling_native_audio.get("external_tts_allowed") is not False:
        errors.append(
            DialogueBeatsValidationError(
                scene_id=scene_id,
                error_code="EXTERNAL_TTS_ALLOWED",
                message="kling_native_audio.external_tts_allowed must be false (const)",
            )
        )
    if kling_native_audio.get("adr_vendor_allowed") is not False:
        errors.append(
            DialogueBeatsValidationError(
                scene_id=scene_id,
                error_code="ADR_VENDOR_ALLOWED",
                message="kling_native_audio.adr_vendor_allowed must be false (const)",
            )
        )

    return errors, blockers


def validate_dialogue_beats_batch(
    records: list[dict[str, Any]], repo_root: str | Path
) -> tuple[dict[str, list[DialogueBeatsValidationError]], dict[str, list[DialogueBeatsReadinessBlocker]]]:
    """
    Validate a batch of dialogue_beats records.

    Args:
        records: list of dialogue_beats dicts
        repo_root: root directory of the repository

    Returns:
        Tuple of (errors_by_scene, blockers_by_scene) where each maps scene_id
        to list of validation failures or readiness blockers.
    """
    errors_by_scene: dict[str, list[DialogueBeatsValidationError]] = {}
    blockers_by_scene: dict[str, list[DialogueBeatsReadinessBlocker]] = {}

    for record in records:
        errors, blockers = validate_dialogue_beats(record, repo_root)
        if errors:
            scene_id = record.get("scene_id", "UNKNOWN")
            errors_by_scene[scene_id] = errors
        if blockers:
            scene_id = record.get("scene_id", "UNKNOWN")
            blockers_by_scene[scene_id] = blockers

    return errors_by_scene, blockers_by_scene
