import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"


@pytest.fixture
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def kling_snapshot():
    return {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260504T140000Z_kling_omni",
        "internal_model_target": "kling_video_best_available",
        "provider": "kling",
        "model_family": "video_generation",
        "provider_surface": "api",
        "observed_at": "2026-05-04T14:00:00Z",
        "expires_at": "2026-05-11T14:00:00Z",
        "human_verified": True,
        "current_default_model": "kling-3.0-omni",
        "latest_available_model": "kling-3.0-omni",
        "best_for_this_task": "kling-3.0-omni",
        "feature_required_model": {
            "multi_shot": "kling-3.0-omni",
            "native_audio": "kling-3.0-omni"
        },
        "version_policy": {
            "hardcode_in_adapter": False,
            "adapter_must_read_snapshot": True,
            "prompt_generation_blocks_if_expired": True,
            "prompt_generation_blocks_if_unverified": True
        },
        "sources": [
            {
                "source_type": "official_docs",
                "title": "Magnific API reference",
                "retrieved_at": "2026-05-04T14:00:00Z",
                "url": "https://docs.magnific.com/api-reference/video/kling-v3-omni/generate-std-video-reference"
            }
        ],
        "capabilities": {
            "output_type": "video",
            "supports_negative_prompt": True,
            "max_duration_seconds": 15,
            "native_fps": 30,
            "native_resolution": "4K"
        },
        "constraints": {
            "max_words_t2v": 60,
            "max_words_i2v": 40
        },
        "prompting_rules": [
            "Write prompts as cinematic shot directions, not visual inventories",
            "Text-to-video: 30-60 words optimal, hard max 100 words"
        ],
        "provenance": {
            "created_by": "human_researcher",
            "created_at": "2026-05-04T14:00:00Z"
        }
    }


@pytest.fixture
def midjourney_snapshot():
    return {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260507T140000Z_midjourney",
        "internal_model_target": "midjourney_image_best_available",
        "provider": "midjourney",
        "model_family": "image_generation",
        "provider_surface": "web_ui",
        "observed_at": "2026-05-07T14:00:00Z",
        "expires_at": "2026-05-14T14:00:00Z",
        "human_verified": True,
        "current_default_model": "v7",
        "latest_available_model": "v8.1",
        "best_for_this_task": "v8.1",
        "feature_required_model": {
            "omni_reference": "v7"
        },
        "version_policy": {
            "hardcode_in_adapter": False,
            "adapter_must_read_snapshot": True,
            "prompt_generation_blocks_if_expired": True,
            "prompt_generation_blocks_if_unverified": True
        },
        "sources": [
            {
                "source_type": "official_docs",
                "title": "Midjourney Version docs",
                "retrieved_at": "2026-05-07T14:00:00Z",
                "url": "https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version"
            }
        ],
        "capabilities": {
            "output_type": "image",
            "supports_negative_prompt": "limited",
            "supports_image_reference": True,
            "current_version": "v8.1"
        },
        "constraints": {
            "max_prompt_tokens": 74
        },
        "prompting_rules": [
            "V8.1 prefers natural language sentences over comma-clause pattern",
            "First 40 words get strongest attention"
        ],
        "provenance": {
            "created_by": "human_researcher",
            "created_at": "2026-05-07T14:00:00Z"
        }
    }


@pytest.fixture
def chatgpt_snapshot():
    return {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260504T113000Z_chatgpt_image",
        "internal_model_target": "chatgpt_image_best_available",
        "provider": "openai",
        "model_family": "image_generation",
        "provider_surface": "chatgpt_ui",
        "observed_at": "2026-05-04T11:30:00Z",
        "expires_at": "2026-05-11T11:30:00Z",
        "human_verified": True,
        "current_default_model": "gpt-image-2",
        "latest_available_model": "gpt-image-2",
        "best_for_this_task": "gpt-image-2",
        "feature_required_model": {
            "multi_panel": "gpt-image-2"
        },
        "version_policy": {
            "hardcode_in_adapter": False,
            "adapter_must_read_snapshot": True,
            "prompt_generation_blocks_if_expired": True,
            "prompt_generation_blocks_if_unverified": True
        },
        "sources": [
            {
                "source_type": "official_docs",
                "title": "OpenAI API image generation guide",
                "retrieved_at": "2026-05-04T11:30:00Z",
                "url": "https://developers.openai.com/api/docs/guides/image-generation"
            }
        ],
        "capabilities": {
            "output_type": "image",
            "supports_negative_prompt": False,
            "supports_natural_language_revision": True,
            "supports_multi_panel": True,
            "current_version": "gpt-image-2"
        },
        "constraints": {
            "max_words_recommended": 200,
            "constraint_strategy": "embedded_positive_constraints"
        },
        "prompting_rules": [
            "Use full, well-formed sentences describing what to create",
            "Embed constraints in positive prompt as explicit prohibitions"
        ],
        "provenance": {
            "created_by": "human_researcher",
            "created_at": "2026-05-04T11:30:00Z"
        }
    }


@pytest.fixture
def nano_banana_snapshot():
    return {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260504T120000Z_nano_banana",
        "internal_model_target": "nano_banana_best_available",
        "provider": "google",
        "model_family": "image_generation",
        "provider_surface": "api",
        "observed_at": "2026-05-04T12:00:00Z",
        "expires_at": "2026-05-11T12:00:00Z",
        "human_verified": True,
        "current_default_model": "gemini-3-pro-image-preview",
        "latest_available_model": "gemini-3-pro-image-preview",
        "best_for_this_task": "gemini-3-pro-image-preview",
        "feature_required_model": {
            "character_consistency": "gemini-3-pro-image-preview"
        },
        "version_policy": {
            "hardcode_in_adapter": False,
            "adapter_must_read_snapshot": True,
            "prompt_generation_blocks_if_expired": True,
            "prompt_generation_blocks_if_unverified": True
        },
        "sources": [
            {
                "source_type": "official_docs",
                "title": "Google Gemini API image generation",
                "retrieved_at": "2026-05-04T12:00:00Z",
                "url": "https://ai.google.dev/gemini-api/docs/image-generation"
            }
        ],
        "capabilities": {
            "output_type": "image",
            "supports_negative_prompt": False,
            "supports_identity_consistency": True,
            "supports_4k": True,
            "max_reference_images": 14,
            "current_version": "gemini-3-pro-image-preview"
        },
        "constraints": {
            "max_prompt_tokens": 480
        },
        "prompting_rules": [
            "Use narrative, descriptive sentences",
            "Use semantic negation embedded in positive prompt"
        ],
        "provenance": {
            "created_by": "human_researcher",
            "created_at": "2026-05-04T12:00:00Z"
        }
    }


class TestSchemaFileExists:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, schema):
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema


class TestValidKlingSnapshot:
    def test_valid_kling_snapshot_structure(self, schema, kling_snapshot):
        from jsonschema import validate
        validate(instance=kling_snapshot, schema=schema)

    def test_kling_has_required_fields(self, kling_snapshot):
        required_fields = {
            "record_type", "schema_version", "snapshot_id",
            "internal_model_target", "provider", "model_family",
            "provider_surface", "observed_at", "expires_at",
            "human_verified", "current_default_model",
            "latest_available_model", "best_for_this_task",
            "feature_required_model", "version_policy", "sources",
            "capabilities", "constraints", "prompting_rules", "provenance"
        }
        assert all(field in kling_snapshot for field in required_fields)


class TestValidMidjourneySnapshot:
    def test_valid_midjourney_snapshot_structure(self, schema, midjourney_snapshot):
        from jsonschema import validate
        validate(instance=midjourney_snapshot, schema=schema)


class TestValidChatGPTSnapshot:
    def test_valid_chatgpt_snapshot_structure(self, schema, chatgpt_snapshot):
        from jsonschema import validate
        validate(instance=chatgpt_snapshot, schema=schema)


class TestValidNanoBananaSnapshot:
    def test_valid_nano_banana_snapshot_structure(self, schema, nano_banana_snapshot):
        from jsonschema import validate
        validate(instance=nano_banana_snapshot, schema=schema)


class TestInvalidRecordType:
    def test_invalid_record_type_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["record_type"] = "wrong_type"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_missing_record_type_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        del bad_snapshot["record_type"]
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestInvalidSchemaVersion:
    def test_invalid_schema_version_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["schema_version"] = "1.0"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestInvalidInternalModelTarget:
    def test_invalid_internal_model_target_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["internal_model_target"] = "unknown_target"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestInvalidProvider:
    def test_invalid_provider_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["provider"] = "anthropic"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestInvalidProviderSurface:
    def test_invalid_provider_surface_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["provider_surface"] = "cloud_console"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestMissingHumanVerified:
    def test_missing_human_verified_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        del bad_snapshot["human_verified"]
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestVersionPolicy:
    def test_hardcode_in_adapter_must_be_false(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["version_policy"]["hardcode_in_adapter"] = True
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_adapter_must_read_snapshot_must_be_true(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["version_policy"]["adapter_must_read_snapshot"] = False
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_prompt_generation_blocks_if_expired_must_be_true(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["version_policy"]["prompt_generation_blocks_if_expired"] = False
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_prompt_generation_blocks_if_unverified_must_be_true(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["version_policy"]["prompt_generation_blocks_if_unverified"] = False
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestSources:
    def test_missing_sources_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        del bad_snapshot["sources"]
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_empty_sources_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["sources"] = []
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)

    def test_source_missing_required_fields_fails(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["sources"] = [
            {
                "source_type": "official_docs",
                "title": "Missing retrieved_at"
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestAdditionalProperties:
    def test_additional_properties_not_allowed(self, schema, kling_snapshot):
        from jsonschema import ValidationError, validate
        bad_snapshot = kling_snapshot.copy()
        bad_snapshot["unknown_field"] = "not_allowed"
        with pytest.raises(ValidationError):
            validate(instance=bad_snapshot, schema=schema)


class TestNullableFields:
    def test_current_default_model_can_be_null(self, schema, kling_snapshot):
        from jsonschema import validate
        good_snapshot = kling_snapshot.copy()
        good_snapshot["current_default_model"] = None
        validate(instance=good_snapshot, schema=schema)

    def test_latest_available_model_can_be_null(self, schema, kling_snapshot):
        from jsonschema import validate
        good_snapshot = kling_snapshot.copy()
        good_snapshot["latest_available_model"] = None
        validate(instance=good_snapshot, schema=schema)

    def test_best_for_this_task_can_be_null(self, schema, kling_snapshot):
        from jsonschema import validate
        good_snapshot = kling_snapshot.copy()
        good_snapshot["best_for_this_task"] = None
        validate(instance=good_snapshot, schema=schema)


class TestAllValidEnums:
    def test_all_internal_model_targets_valid(self, schema, kling_snapshot):
        from jsonschema import validate
        targets = [
            "kling_video_best_available",
            "midjourney_image_best_available",
            "chatgpt_image_best_available",
            "nano_banana_best_available"
        ]
        for target in targets:
            good_snapshot = kling_snapshot.copy()
            good_snapshot["internal_model_target"] = target
            validate(instance=good_snapshot, schema=schema)

    def test_all_providers_valid(self, schema, kling_snapshot):
        from jsonschema import validate
        providers = ["kling", "midjourney", "openai", "google"]
        for provider in providers:
            good_snapshot = kling_snapshot.copy()
            good_snapshot["provider"] = provider
            validate(instance=good_snapshot, schema=schema)

    def test_all_provider_surfaces_valid(self, schema, kling_snapshot):
        from jsonschema import validate
        surfaces = [
            "web_ui", "api", "app", "manual_external", "chatgpt_ui", "gemini_app"
        ]
        for surface in surfaces:
            good_snapshot = kling_snapshot.copy()
            good_snapshot["provider_surface"] = surface
            validate(instance=good_snapshot, schema=schema)
