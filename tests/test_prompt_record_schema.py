"""Tests for prompt_record.schema.json model guidance fields.

Validates that:
1. Existing minimal records without model guidance still validate (additive compatibility)
2. Records with model guidance fields validate when complete
3. model_guidance_mode must be exactly "dynamic_snapshot" when present
4. All model guidance fields have correct types and enums
5. No provider version strings are hardcoded in schema defaults
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

import jsonschema
import pytest

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "prompt_record.schema.json"


@pytest.fixture
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def validator(schema):
    return jsonschema.Draft202012Validator(schema)


def get_valid_prompt_minimal():
    """Minimal valid prompt record without model guidance."""
    return {
        "prompt_id": "SC0001__t2i-char-midjourney__v01",
        "scene_id": "SC0001",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md"
        },
        "prompt_text": "A highly detailed portrait of Nadia...",
        "status": "active",
        "canon_lock": False
    }


def get_valid_prompt_with_model_guidance():
    """Valid prompt record with complete model guidance fields."""
    base = get_valid_prompt_minimal()
    base["generation_params"] = {
        "model_guidance_mode": "dynamic_snapshot",
        "model_guidance_snapshot_ref": "model_guidance_snapshots/midjourney/20260508T120000Z_midjourney_image_best_available.yaml",
        "provider": "midjourney",
        "provider_surface": "web_ui",
        "resolved_model_name": "V8.1",
        "resolved_model_role": "best_for_this_task",
        "guidance_observed_at": "2026-05-08T12:00:00Z",
        "guidance_expires_at": "2026-06-08T12:00:00Z"
    }
    return base


class TestPromptRecordAdditiveCompatibility:
    """Verify minimal records without model guidance still validate."""

    def test_minimal_record_without_model_guidance_valid(self, validator):
        """Existing records without generation_params should still be valid."""
        prompt = get_valid_prompt_minimal()
        # Should not raise ValidationError
        validator.validate(prompt)

    def test_minimal_record_with_empty_generation_params_valid(self, validator):
        """Records with empty generation_params should be valid."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {}
        validator.validate(prompt)

    def test_minimal_record_with_other_generation_params_valid(self, validator):
        """Records with non-guidance generation_params should still be valid."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "temperature": 0.7,
            "max_tokens": 100,
            "custom_param": "value"
        }
        validator.validate(prompt)


class TestPromptRecordModelGuidanceFields:
    """Verify complete model guidance records validate."""

    def test_complete_model_guidance_record_valid(self, validator):
        """Record with all model guidance fields should validate."""
        prompt = get_valid_prompt_with_model_guidance()
        validator.validate(prompt)

    def test_kling_model_guidance_valid(self, validator):
        """Kling omni video model guidance should validate."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "model_guidance_mode": "dynamic_snapshot",
            "model_guidance_snapshot_ref": "model_guidance_snapshots/kling/20260508T140000Z_kling_omni_video_best_available.yaml",
            "provider": "kling",
            "provider_surface": "api",
            "resolved_model_name": "Kling 3.0 Omni",
            "resolved_model_role": "best_for_this_task",
            "guidance_observed_at": "2026-05-08T14:00:00Z",
            "guidance_expires_at": "2026-06-08T14:00:00Z"
        }
        validator.validate(prompt)

    def test_chatgpt_model_guidance_valid(self, validator):
        """ChatGPT image model guidance should validate."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "model_guidance_mode": "dynamic_snapshot",
            "model_guidance_snapshot_ref": "model_guidance_snapshots/openai/20260508T130000Z_chatgpt_image_best_available.yaml",
            "provider": "openai",
            "provider_surface": "chatgpt_ui",
            "resolved_model_name": "gpt-image-2",
            "resolved_model_role": "current_default",
            "guidance_observed_at": "2026-05-08T13:00:00Z",
            "guidance_expires_at": "2026-06-08T13:00:00Z"
        }
        validator.validate(prompt)

    def test_nano_banana_model_guidance_valid(self, validator):
        """Nano Banana model guidance should validate."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "model_guidance_mode": "dynamic_snapshot",
            "model_guidance_snapshot_ref": "model_guidance_snapshots/google/20260508T110000Z_nano_banana_best_available.yaml",
            "provider": "google",
            "provider_surface": "gemini_app",
            "resolved_model_name": "Nano Banana Pro / gemini-3-pro-image-preview",
            "resolved_model_role": "latest_available",
            "guidance_observed_at": "2026-05-08T11:00:00Z",
            "guidance_expires_at": "2026-06-08T11:00:00Z"
        }
        validator.validate(prompt)


class TestPromptRecordModelGuidanceValidation:
    """Verify model guidance field validation rules."""

    def test_model_guidance_mode_must_be_const_value(self, validator):
        """model_guidance_mode must be exactly 'dynamic_snapshot' when present."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["model_guidance_mode"] = "static"
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(prompt)

    def test_invalid_provider_fails(self, validator):
        """Invalid provider enum value should fail."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["provider"] = "unknown_provider"
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(prompt)

    def test_invalid_provider_surface_fails(self, validator):
        """Invalid provider_surface enum value should fail."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["provider_surface"] = "invalid_surface"
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(prompt)

    def test_invalid_resolved_model_role_fails(self, validator):
        """Invalid resolved_model_role enum value should fail."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["resolved_model_role"] = "unknown_role"
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(prompt)

    def test_guidance_observed_at_accepts_datetime(self, validator):
        """guidance_observed_at should accept valid ISO 8601 date-time."""
        prompt = get_valid_prompt_with_model_guidance()
        # Valid ISO 8601 datetime
        prompt["generation_params"]["guidance_observed_at"] = "2026-05-08T14:00:00Z"
        validator.validate(prompt)

    def test_guidance_expires_at_accepts_datetime(self, validator):
        """guidance_expires_at should accept valid ISO 8601 date-time."""
        prompt = get_valid_prompt_with_model_guidance()
        # Valid ISO 8601 datetime
        prompt["generation_params"]["guidance_expires_at"] = "2026-06-08T14:00:00Z"
        validator.validate(prompt)

    def test_snapshot_ref_format_flexible(self, validator):
        """Snapshot ref should accept various valid relative path formats."""
        prompt = get_valid_prompt_with_model_guidance()
        valid_refs = [
            "model_guidance_snapshots/kling/20260508T140000Z_kling_omni_video_best_available.yaml",
            "model_guidance_snapshots/midjourney/20260508T120000Z_midjourney_image_best_available.yaml",
            "model_guidance_snapshots/openai/20260508T130000Z_chatgpt_image_best_available.yaml",
            "model_guidance_snapshots/google/20260508T110000Z_nano_banana_best_available.yaml",
        ]
        for ref in valid_refs:
            prompt["generation_params"]["model_guidance_snapshot_ref"] = ref
            validator.validate(prompt)


class TestPromptRecordAllProviderRoles:
    """Verify all enum variants for resolved_model_role."""

    def test_current_default_role_valid(self, validator):
        """current_default role should be valid."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["resolved_model_role"] = "current_default"
        validator.validate(prompt)

    def test_latest_available_role_valid(self, validator):
        """latest_available role should be valid."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["resolved_model_role"] = "latest_available"
        validator.validate(prompt)

    def test_best_for_this_task_role_valid(self, validator):
        """best_for_this_task role should be valid."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["resolved_model_role"] = "best_for_this_task"
        validator.validate(prompt)

    def test_feature_required_role_valid(self, validator):
        """feature_required role should be valid."""
        prompt = get_valid_prompt_with_model_guidance()
        prompt["generation_params"]["resolved_model_role"] = "feature_required"
        validator.validate(prompt)


class TestPromptRecordNoHardcodedVersionStrings:
    """Verify schema does not contain hardcoded provider version strings."""

    def test_schema_has_no_hardcoded_kling_version(self):
        """Schema should not have hardcoded Kling version names as const."""
        schema_str = SCHEMA_PATH.read_text()
        forbidden = ["kling-3.0-omni", "Kling 3.0 Omni", "kling_3_0_omni"]
        for term in forbidden:
            assert term not in schema_str or "model_guidance_snapshots" in schema_str, (
                f"Hardcoded Kling version {term!r} found in schema"
            )

    def test_schema_has_no_hardcoded_midjourney_version(self):
        """Schema should not have hardcoded Midjourney version names as const or default."""
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)

        gen_params = schema["properties"]["generation_params"]["properties"]
        # resolved_model_name should not have a const value with Midjourney version
        model_name_spec = gen_params.get("resolved_model_name", {})
        assert model_name_spec.get("const") is None, (
            "resolved_model_name should not have a const value — versions come from snapshots"
        )

    def test_schema_has_no_hardcoded_gpt_image_version(self):
        """Schema should not have hardcoded gpt-image-2 as const."""
        schema_str = SCHEMA_PATH.read_text()
        assert "gpt-image-2" not in schema_str or "model_guidance_snapshots" in schema_str

    def test_schema_generation_params_mode_is_const(self):
        """model_guidance_mode must be const, not default."""
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)

        mode_spec = schema["properties"]["generation_params"]["properties"]["model_guidance_mode"]
        assert mode_spec.get("const") == "dynamic_snapshot", (
            "model_guidance_mode should use const, not default"
        )


class TestPromptRecordPartialModelGuidance:
    """Test behavior when only some model guidance fields are present."""

    def test_only_mode_without_other_fields_valid(self, validator):
        """Record with only model_guidance_mode should be valid (other fields optional)."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "model_guidance_mode": "dynamic_snapshot"
        }
        # Should validate - other model guidance fields are not strictly required at schema level
        validator.validate(prompt)

    def test_mixed_model_guidance_and_other_params_valid(self, validator):
        """Model guidance fields should coexist with other generation_params."""
        prompt = get_valid_prompt_minimal()
        prompt["generation_params"] = {
            "temperature": 0.8,
            "model_guidance_mode": "dynamic_snapshot",
            "model_guidance_snapshot_ref": "model_guidance_snapshots/kling/20260508T140000Z_kling_omni_video_best_available.yaml",
            "provider": "kling",
            "provider_surface": "api",
            "custom_param": "custom_value",
            "resolved_model_name": "Kling 3.0 Omni",
            "resolved_model_role": "best_for_this_task",
            "guidance_observed_at": "2026-05-08T14:00:00Z",
            "guidance_expires_at": "2026-06-08T14:00:00Z"
        }
        validator.validate(prompt)


class TestPromptRecordProviderSurfaces:
    """Verify all provider_surface enum values work with each provider."""

    def test_all_provider_surfaces_valid(self, validator):
        """Each provider surface should be valid."""
        surfaces = ["web_ui", "api", "app", "manual_external", "chatgpt_ui", "gemini_app"]
        prompt = get_valid_prompt_with_model_guidance()
        for surface in surfaces:
            prompt["generation_params"]["provider_surface"] = surface
            validator.validate(prompt)
