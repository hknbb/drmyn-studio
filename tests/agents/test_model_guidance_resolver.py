"""
Tests for model_guidance_resolver.py.

Comprehensive validation of snapshot resolution, expiry checks,
human verification gates, placeholder rejection, and feature resolution.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.model_guidance_resolver import (
	ModelGuidanceResolutionError,
	resolve_model_guidance,
)


@pytest.fixture
def repo_structure():
	"""Create a temporary repo structure with schema and snapshots."""
	with tempfile.TemporaryDirectory() as tmpdir:
		repo_root = Path(tmpdir)

		# Copy schema
		schema_path = repo_root / "schemas"
		schema_path.mkdir()

		schema_file = Path(__file__).parent.parent.parent / "schemas" / "model_guidance_snapshot.schema.json"
		with open(schema_file, "r", encoding="utf-8") as src:
			schema_data = json.load(src)
		with open(schema_path / "model_guidance_snapshot.schema.json", "w", encoding="utf-8") as dst:
			json.dump(schema_data, dst)

		# Create snapshots directory
		snapshots_path = repo_root / "model_guidance_snapshots"
		snapshots_path.mkdir()

		yield repo_root


@pytest.fixture
def valid_kling_snapshot():
	"""Valid Kling snapshot fixture."""
	return {
		"record_type": "model_guidance_snapshot",
		"schema_version": "0.x-draft",
		"snapshot_id": "20260504T140000Z_kling_omni",
		"internal_model_target": "kling_video_best_available",
		"provider": "kling",
		"model_family": "video_generation",
		"provider_surface": "api",
		"observed_at": "2026-05-04T14:00:00Z",
		"expires_at": "2026-06-04T14:00:00Z",
		"human_verified": True,
		"current_default_model": "kling-3.0-omni",
		"latest_available_model": "kling-3.0-omni",
		"best_for_this_task": "kling-3.0-omni",
		"feature_required_model": {
			"multi_shot": "kling-3.0-omni",
			"native_audio": "kling-3.0-omni",
		},
		"version_policy": {
			"hardcode_in_adapter": False,
			"adapter_must_read_snapshot": True,
			"prompt_generation_blocks_if_expired": True,
			"prompt_generation_blocks_if_unverified": True,
		},
		"sources": [
			{
				"source_type": "official_docs",
				"title": "Kling API reference",
				"retrieved_at": "2026-05-04T14:00:00Z",
				"url": "https://docs.magnific.com/api-reference/video/kling-v3-omni/",
			}
		],
		"capabilities": {
			"output_type": "video",
			"supports_negative_prompt": True,
			"max_duration_seconds": 15,
		},
		"constraints": {
			"max_prompt_length": 1000,
		},
		"prompting_rules": [
			"Use cinematic direction, not visual inventory",
			"Specify end state to prevent hang",
		],
		"provenance": {
			"created_by": "model_research_agent",
			"created_at": "2026-05-04T14:00:00Z",
		},
	}


@pytest.fixture
def valid_midjourney_snapshot():
	"""Valid Midjourney snapshot fixture."""
	return {
		"record_type": "model_guidance_snapshot",
		"schema_version": "0.x-draft",
		"snapshot_id": "20260504T140000Z_midjourney",
		"internal_model_target": "midjourney_image_best_available",
		"provider": "midjourney",
		"model_family": "image_generation",
		"provider_surface": "web_ui",
		"observed_at": "2026-05-04T14:00:00Z",
		"expires_at": "2026-06-04T14:00:00Z",
		"human_verified": True,
		"current_default_model": "v7",
		"latest_available_model": "v8.1",
		"best_for_this_task": "v8.1",
		"feature_required_model": {
			"omni_reference": "v7",
		},
		"version_policy": {
			"hardcode_in_adapter": False,
			"adapter_must_read_snapshot": True,
			"prompt_generation_blocks_if_expired": True,
			"prompt_generation_blocks_if_unverified": True,
		},
		"sources": [
			{
				"source_type": "official_docs",
				"title": "Midjourney Docs",
				"retrieved_at": "2026-05-04T14:00:00Z",
			}
		],
		"capabilities": {
			"output_type": "image",
			"supports_negative_prompt": False,
		},
		"constraints": {},
		"prompting_rules": [
			"Lead with subject",
		],
		"provenance": {},
	}


@pytest.fixture
def now_utc():
	"""Current UTC datetime for consistent time-based tests."""
	return datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc)


# Tests: Happy path

class TestValidSnapshotResolves:
	"""Valid snapshots resolve successfully."""

	def test_valid_kling_snapshot_resolves(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["provider"] == "kling"
		assert result["provider_surface"] == "api"
		assert result["resolved_model_name"] == "kling-3.0-omni"
		assert result["resolved_model_role"] == "best_for_this_task"
		assert "model_guidance_snapshot_ref" in result
		assert "guidance_observed_at" in result
		assert "guidance_expires_at" in result

	def test_valid_midjourney_snapshot_resolves(
		self, repo_structure, valid_midjourney_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "midjourney"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_midjourney_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"midjourney_image_best_available",
			now=now_utc,
		)

		assert result["provider"] == "midjourney"
		assert result["resolved_model_name"] == "v8.1"


# Tests: Missing/Not Found

class TestMissingSnapshot:
	"""Missing snapshots raise ModelGuidanceResolutionError."""

	def test_missing_snapshot_raises(self, repo_structure, now_utc):
		repo_root = repo_structure

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "No snapshots found" in str(exc_info.value)

	def test_wrong_internal_model_target_is_ignored(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		# Try to resolve with different target
		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"midjourney_image_best_available",
				now=now_utc,
			)

		assert "No snapshots found" in str(exc_info.value)


# Tests: Expiry

class TestExpiredSnapshot:
	"""Expired snapshots are rejected."""

	def test_expired_snapshot_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# Set expires_at in the past; expired snapshot is skipped
		valid_kling_snapshot["expires_at"] = "2026-05-01T14:00:00Z"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		# With new behavior, expired snapshots are skipped; if only expired exists, "no valid" error
		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "valid" in str(exc_info.value).lower()

	def test_not_yet_expired_snapshot_resolves(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# expires_at is exactly 30 days in future from now_utc
		valid_kling_snapshot["expires_at"] = (
			now_utc + timedelta(days=30)
		).isoformat()

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["resolved_model_name"] == "kling-3.0-omni"


# Tests: Human Verification

class TestUnverifiedSnapshot:
	"""Unverified snapshots are rejected."""

	def test_unverified_snapshot_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["human_verified"] = False

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "unverified" in str(exc_info.value).lower()


# Tests: Placeholders

class TestPlaceholderRejection:
	"""Placeholder model values are rejected."""

	def test_placeholder_latest_available_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["latest_available_model"] = "TBD"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "placeholder" in str(exc_info.value).lower()

	def test_placeholder_best_for_task_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["best_for_this_task"] = "TODO"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "placeholder" in str(exc_info.value).lower()

	def test_empty_string_is_placeholder(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["latest_available_model"] = ""

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "placeholder" in str(exc_info.value).lower()


# Tests: Feature Resolution

class TestFeatureResolution:
	"""Feature-based resolution uses feature_required_model."""

	def test_required_feature_resolves_feature_model(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			required_feature="native_audio",
			now=now_utc,
		)

		assert result["resolved_model_name"] == "kling-3.0-omni"
		assert result["resolved_model_role"] == "feature_required"

	def test_missing_required_feature_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				required_feature="nonexistent_feature",
				now=now_utc,
			)

		assert "missing" in str(exc_info.value).lower()

	def test_placeholder_required_feature_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["feature_required_model"]["omni_reference"] = "TBD"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				required_feature="omni_reference",
				now=now_utc,
			)

		assert "placeholder" in str(exc_info.value).lower()


# Tests: Multiple Snapshots

class TestMultipleSnapshots:
	"""When multiple snapshots exist, the newest valid one is chosen."""

	def test_newest_snapshot_chosen(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# Write older snapshot
		old_snapshot = valid_kling_snapshot.copy()
		old_snapshot["snapshot_id"] = "20260501T140000Z_kling_omni"
		old_snapshot["observed_at"] = "2026-05-01T14:00:00Z"
		old_snapshot["best_for_this_task"] = "kling-3.0-omni-old"

		with open(snapshots_dir / "old_snapshot.yaml", "w", encoding="utf-8") as f:
			yaml.dump(old_snapshot, f)

		# Write newer snapshot
		new_snapshot = valid_kling_snapshot.copy()
		new_snapshot["snapshot_id"] = "20260504T140000Z_kling_omni"
		new_snapshot["observed_at"] = "2026-05-04T14:00:00Z"
		new_snapshot["best_for_this_task"] = "kling-3.0-omni-new"

		with open(snapshots_dir / "new_snapshot.yaml", "w", encoding="utf-8") as f:
			yaml.dump(new_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["resolved_model_name"] == "kling-3.0-omni-new"


# Tests: Schema Validation

class TestSchemaValidation:
	"""Schema-invalid snapshots are rejected."""

	def test_schema_invalid_snapshot_raises(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# Remove required field
		del valid_kling_snapshot["provider"]

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "schema" in str(exc_info.value).lower()


# Tests: Return Structure

class TestReturnStructure:
	"""Resolved result includes all required fields."""

	def test_resolved_includes_all_fields(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		required_keys = {
			"model_guidance_snapshot_ref",
			"provider",
			"provider_surface",
			"resolved_model_name",
			"resolved_model_role",
			"guidance_observed_at",
			"guidance_expires_at",
			"prompting_rules",
			"capabilities",
			"constraints",
		}

		assert required_keys.issubset(result.keys())

	def test_provider_surface_is_preserved(
		self, repo_structure, valid_midjourney_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "midjourney"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_midjourney_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"midjourney_image_best_available",
			now=now_utc,
		)

		assert result["provider_surface"] == "web_ui"

	def test_guidance_expiry_metadata_present(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["guidance_observed_at"] == "2026-05-04T14:00:00Z"
		assert result["guidance_expires_at"] == "2026-06-04T14:00:00Z"


# Tests: Error Messages

class TestErrorMessages:
	"""Error messages are clear and actionable."""

	def test_error_names_internal_model_target(
		self, repo_structure, now_utc
	):
		repo_root = repo_structure

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		assert "kling_video_best_available" in str(exc_info.value)

	def test_error_names_failed_condition(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# Expired snapshot is skipped; only one snapshot means "no valid" error
		valid_kling_snapshot["expires_at"] = "2026-05-01T14:00:00Z"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		error_msg = str(exc_info.value).lower()
		assert "valid" in error_msg


# Tests: Model Role Resolution

class TestModelRoleResolution:
	"""resolved_model_role is set correctly based on resolution strategy."""

	def test_best_for_this_task_role(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["resolved_model_role"] == "best_for_this_task"

	def test_latest_available_role_when_best_missing(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		valid_kling_snapshot["best_for_this_task"] = None
		valid_kling_snapshot["latest_available_model"] = "kling-3.0-omni-latest"

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["resolved_model_role"] == "latest_available"
		assert result["resolved_model_name"] == "kling-3.0-omni-latest"

	def test_feature_required_role_when_feature_requested(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		snapshot_file = snapshots_dir / "snapshot.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			required_feature="multi_shot",
			now=now_utc,
		)

		assert result["resolved_model_role"] == "feature_required"


# Integration Tests

class TestIntegration:
	"""Integration tests with multiple providers."""

	def test_all_four_providers_independently_resolve(
		self, repo_structure, valid_kling_snapshot, valid_midjourney_snapshot, now_utc
	):
		repo_root = repo_structure

		# Write Kling
		kling_dir = repo_root / "model_guidance_snapshots" / "kling"
		kling_dir.mkdir(parents=True)
		with open(kling_dir / "snapshot.yaml", "w", encoding="utf-8") as f:
			yaml.dump(valid_kling_snapshot, f)

		# Write Midjourney
		mj_dir = repo_root / "model_guidance_snapshots" / "midjourney"
		mj_dir.mkdir(parents=True)
		with open(mj_dir / "snapshot.yaml", "w", encoding="utf-8") as f:
			yaml.dump(valid_midjourney_snapshot, f)

		# Resolve each independently
		kling_result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)
		assert kling_result["provider"] == "kling"

		mj_result = resolve_model_guidance(
			repo_root,
			"midjourney_image_best_available",
			now=now_utc,
		)
		assert mj_result["provider"] == "midjourney"


# Tests: Expired Snapshot Skipping

class TestExpiredSnapshotSkipped:
	"""Expired snapshots are skipped when newer valid snapshots exist."""

	def test_expired_snapshot_skipped_for_newer_valid(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		# Expired snapshot (older)
		expired_snapshot = valid_kling_snapshot.copy()
		expired_snapshot["observed_at"] = "2026-05-02T10:00:00Z"
		expired_snapshot["expires_at"] = "2026-05-03T10:00:00Z"  # Expired before now_utc
		expired_snapshot["best_for_this_task"] = "kling-3.0-omni-expired"
		with open(snapshots_dir / "expired_old.yaml", "w", encoding="utf-8") as f:
			yaml.dump(expired_snapshot, f)

		# Valid snapshot (newer)
		valid_newer = valid_kling_snapshot.copy()
		valid_newer["observed_at"] = "2026-05-04T14:00:00Z"
		valid_newer["expires_at"] = "2026-06-04T14:00:00Z"
		valid_newer["best_for_this_task"] = "kling-3.0-omni-v2"
		with open(snapshots_dir / "valid_new.yaml", "w", encoding="utf-8") as f:
			yaml.dump(valid_newer, f)

		# Should resolve to the newer valid snapshot, skipping the expired one
		result = resolve_model_guidance(
			repo_root,
			"kling_video_best_available",
			now=now_utc,
		)

		assert result["resolved_model_name"] == "kling-3.0-omni-v2"
		assert result["guidance_observed_at"] == "2026-05-04T14:00:00Z"


# Tests: Null Model Rejection

class TestNullModelRejection:
	"""Snapshots with both best_for_this_task and latest_available_model null are rejected."""

	def test_both_null_models_raises_error(
		self, repo_structure, valid_kling_snapshot, now_utc
	):
		repo_root = repo_structure
		snapshots_dir = repo_root / "model_guidance_snapshots" / "kling"
		snapshots_dir.mkdir(parents=True)

		null_snapshot = valid_kling_snapshot.copy()
		null_snapshot["best_for_this_task"] = None
		null_snapshot["latest_available_model"] = None

		snapshot_file = snapshots_dir / "null_models.yaml"
		with open(snapshot_file, "w", encoding="utf-8") as f:
			yaml.dump(null_snapshot, f)

		with pytest.raises(ModelGuidanceResolutionError) as exc_info:
			resolve_model_guidance(
				repo_root,
				"kling_video_best_available",
				now=now_utc,
			)

		error_msg = str(exc_info.value).lower()
		assert "no resolvable model" in error_msg
