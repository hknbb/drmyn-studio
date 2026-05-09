"""
Tests for A7.1 BaseAdapter model guidance resolution.

Validates:
1. Dynamic snapshot mode resolves model names from snapshots
2. Resolved fields are populated in generation_params
3. Missing/expired/unverified snapshots block generation
4. Locked_guide mode preserves backwards compatibility
5. Adapter must set INTERNAL_MODEL_TARGET when using dynamic_snapshot mode
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.adapters._base import BaseAdapter
from scripts.agents.model_guidance_resolver import ModelGuidanceResolutionError
from scripts.agents.neutral_brief import NeutralBrief


REPO_ROOT = Path(__file__).parent.parent.parent


class MockAdapter(BaseAdapter):
    """Minimal mock adapter."""

    MODEL_ID = "test_model"
    MODEL_SLUG = "test-model"
    ABBREV = "TM"

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        return "Test prompt"


class MockAdapterDynamicSnapshot(BaseAdapter):
    """Mock adapter with dynamic snapshot mode."""

    MODEL_ID = "test_model_dynamic"
    MODEL_SLUG = "test-model-dynamic"
    ABBREV = "TMD"
    INTERNAL_MODEL_TARGET = "nano_banana_best_available"

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        return "Test prompt dynamic"


class MockBrief:
    """Minimal NeutralBrief for testing."""

    def __init__(self):
        self.is_ready = True
        self.element_type = "character"
        self.element_id = "C01"
        self.element_name = "Nadia"
        self.scene_id = "SC0001"
        self.warnings = []
        self.continuity_state = None
        self.visual_anchors = []
        self.aesthetic_keywords = []
        self.negative_constraints = []
        self.planning_aliases = []
        self.aesthetic_pack_refs = []
        self.prompt_subject_label = None


class TestLockedGuideModeBackwardsCompat:
    """Verify locked_guide mode (legacy) still works."""

    def test_locked_guide_default_mode(self):
        """Default mode should be locked_guide."""
        adapter = MockAdapter(REPO_ROOT)
        assert adapter.model_guidance_mode == "locked_guide"

    def test_locked_guide_generation_params(self):
        """Locked guide mode should populate legacy fields."""
        adapter = MockAdapter(REPO_ROOT)
        brief = MockBrief()

        params = adapter._generation_params(brief)

        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_ref"] == "docs/model_guides/test_model.yaml"
        assert params["adapter_name"] == "test_model"
        assert "model_guidance_snapshot_ref" not in params
        assert "resolved_model_name" not in params

    def test_locked_guide_with_snapshot_parameter(self):
        """Locked guide can optionally include snapshot parameter."""
        adapter = MockAdapter(
            REPO_ROOT,
            model_guidance_snapshot="model_guidance_snapshots/test/2026-05-09T12:00:00Z__test.yaml",
        )
        brief = MockBrief()

        params = adapter._generation_params(brief)

        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_snapshot"] == "model_guidance_snapshots/test/2026-05-09T12:00:00Z__test.yaml"


class TestDynamicSnapshotModeResolution:
    """Test dynamic_snapshot mode with model resolution."""

    def _create_test_snapshot(self, tmpdir: Path, target: str, **overrides) -> Path:
        """Helper to create a valid test snapshot."""
        snapshots_dir = tmpdir / "model_guidance_snapshots" / "google"
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30)

        snapshot = {
            "record_type": "model_guidance_snapshot",
            "schema_version": "0.x-draft",
            "snapshot_id": f"{target}__2026-05-09",
            "internal_model_target": target,
            "provider": "google",
            "model_family": "image_generation",
            "provider_surface": "gemini_app",
            "observed_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "human_verified": True,
            "current_default_model": "test-model-v1",
            "latest_available_model": "test-model-v2",
            "best_for_this_task": "test-model-v2",
            "feature_required_model": {},
            "version_policy": {
                "hardcode_in_adapter": False,
                "adapter_must_read_snapshot": True,
                "prompt_generation_blocks_if_expired": True,
                "prompt_generation_blocks_if_unverified": True,
            },
            "sources": [
                {
                    "source_type": "official_docs",
                    "title": "Test Source",
                    "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                    "url": "https://example.com/docs",
                }
            ],
            "capabilities": {"feature_a": True},
            "constraints": {"max_tokens": 500},
            "prompting_rules": [],
            "provenance": {
                "created_by": "test",
                "created_at": now.isoformat().replace("+00:00", "Z"),
            },
        }
        snapshot.update(overrides)

        # Use the target name for the filename for clarity
        snapshot_file = snapshots_dir / f"2026-05-09T120000Z__{target}.yaml"
        with open(snapshot_file, "w") as f:
            yaml.dump(snapshot, f)

        return snapshot_file

    def _create_test_schema(self, tmpdir: Path) -> Path:
        """Helper to create minimal schema."""
        schemas_dir = tmpdir / "schemas"
        schemas_dir.mkdir(parents=True, exist_ok=True)

        # Read actual schema from repo
        actual_schema_path = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"
        if actual_schema_path.exists():
            with open(actual_schema_path) as f:
                schema = json.load(f)
        else:
            # Minimal fallback schema
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "record_type": {"type": "string"},
                    "snapshot_id": {"type": "string"},
                    "internal_model_target": {"type": "string"},
                    "provider": {"type": "string"},
                    "model_family": {"type": "string"},
                    "provider_surface": {"type": "string"},
                    "observed_at": {"type": "string"},
                    "expires_at": {"type": "string"},
                    "human_verified": {"type": "boolean"},
                    "current_default_model": {"type": ["string", "null"]},
                    "latest_available_model": {"type": ["string", "null"]},
                    "best_for_this_task": {"type": ["string", "null"]},
                    "feature_required_model": {"type": "object"},
                    "version_policy": {"type": "object"},
                    "sources": {"type": "array"},
                    "capabilities": {"type": "object"},
                    "constraints": {"type": "object"},
                    "prompting_rules": {"type": "array"},
                },
            }

        schema_file = schemas_dir / "model_guidance_snapshot.schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema, f, indent=2)

        return schema_file

    def test_dynamic_snapshot_mode_resolves(self):
        """Dynamic snapshot mode should resolve model from snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create schema
            self._create_test_schema(tmpdir_path)

            # Create valid snapshot
            self._create_test_snapshot(
                tmpdir_path,
                "nano_banana_best_available",
            )

            # Create adapter with dynamic mode
            adapter = MockAdapterDynamicSnapshot(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            params = adapter._generation_params(brief)

            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert params["resolved_model_name"] == "test-model-v2"
            assert params["resolved_model_role"] == "best_for_this_task"
            assert params["provider"] == "google"
            assert params["provider_surface"] == "gemini_app"
            assert "model_guidance_snapshot_ref" in params
            assert "guidance_observed_at" in params
            assert "guidance_expires_at" in params

    def test_dynamic_snapshot_missing_snapshot_blocks(self):
        """Missing snapshot should block generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create schema but no snapshot
            self._create_test_schema(tmpdir_path)

            adapter = MockAdapterDynamicSnapshot(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            with pytest.raises(
                ModelGuidanceResolutionError,
                match="No snapshots found for internal_model_target",
            ):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_expired_snapshot_blocked(self):
        """Expired snapshot should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create schema
            self._create_test_schema(tmpdir_path)

            # Create expired snapshot (expires in past)
            now = datetime.now(timezone.utc)
            expired_at = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")

            self._create_test_snapshot(
                tmpdir_path,
                "nano_banana_best_available",
                expires_at=expired_at,
            )

            adapter = MockAdapterDynamicSnapshot(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            with pytest.raises(
                ModelGuidanceResolutionError,
                match="No valid snapshot found",
            ):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_unverified_snapshot_blocked(self):
        """Unverified snapshot should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create schema
            self._create_test_schema(tmpdir_path)

            # Create unverified snapshot
            self._create_test_snapshot(
                tmpdir_path,
                "nano_banana_best_available",
                human_verified=False,
            )

            adapter = MockAdapterDynamicSnapshot(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            with pytest.raises(ModelGuidanceResolutionError, match="is unverified"):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_missing_internal_target(self):
        """Adapter without INTERNAL_MODEL_TARGET should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            self._create_test_schema(tmpdir_path)

            # Create adapter with dynamic mode but no INTERNAL_MODEL_TARGET
            adapter = MockAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            with pytest.raises(ValueError, match="INTERNAL_MODEL_TARGET is not set"):
                adapter._generation_params(brief)


class TestResolveModelMethod:
    """Test _resolve_model() method."""

    def test_resolve_model_delegates_to_resolver(self):
        """_resolve_model() should call resolver and return dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create schema and snapshot
            schemas_dir = tmpdir_path / "schemas"
            schemas_dir.mkdir(parents=True, exist_ok=True)
            actual_schema_path = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"
            if actual_schema_path.exists():
                with open(actual_schema_path) as f:
                    schema = json.load(f)
                schema_file = schemas_dir / "model_guidance_snapshot.schema.json"
                with open(schema_file, "w") as f:
                    json.dump(schema, f)

            snapshots_dir = tmpdir_path / "model_guidance_snapshots" / "google"
            snapshots_dir.mkdir(parents=True, exist_ok=True)

            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(days=30)).isoformat().replace("+00:00", "Z")

            snapshot = {
                "record_type": "model_guidance_snapshot",
                "schema_version": "0.x-draft",
                "snapshot_id": "nano_banana__2026-05-09",
                "internal_model_target": "nano_banana_best_available",
                "provider": "google",
                "model_family": "image_generation",
                "provider_surface": "gemini_app",
                "observed_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": expires_at,
                "human_verified": True,
                "current_default_model": "Nano Banana Pro v1",
                "latest_available_model": "Nano Banana Pro v2",
                "best_for_this_task": "Nano Banana Pro v2",
                "feature_required_model": {},
                "version_policy": {
                    "hardcode_in_adapter": False,
                    "adapter_must_read_snapshot": True,
                    "prompt_generation_blocks_if_expired": True,
                    "prompt_generation_blocks_if_unverified": True,
                },
                "sources": [
                    {
                        "source_type": "official_docs",
                        "title": "Test",
                        "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                        "url": "https://example.com",
                    }
                ],
                "capabilities": {},
                "constraints": {},
                "prompting_rules": [],
                "provenance": {
                    "created_by": "test",
                    "created_at": now.isoformat().replace("+00:00", "Z"),
                },
            }

            snapshot_file = snapshots_dir / "2026-05-09T120000Z__nano_banana_best_available.yaml"
            with open(snapshot_file, "w") as f:
                yaml.dump(snapshot, f)

            adapter = MockAdapter(tmpdir_path)
            result = adapter._resolve_model("nano_banana_best_available")

            assert isinstance(result, dict)
            assert result["resolved_model_name"] == "Nano Banana Pro v2"
            assert result["resolved_model_role"] == "best_for_this_task"
            assert result["provider"] == "google"


class TestGenerateWithDynamicSnapshot:
    """Test full generate() flow with dynamic snapshot resolution."""

    def test_generate_with_dynamic_snapshot(self):
        """Full generate() should work with dynamic snapshot mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Setup schema and snapshot
            schemas_dir = tmpdir_path / "schemas"
            schemas_dir.mkdir(parents=True, exist_ok=True)
            actual_schema_path = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"
            if actual_schema_path.exists():
                with open(actual_schema_path) as f:
                    schema = json.load(f)
                schema_file = schemas_dir / "model_guidance_snapshot.schema.json"
                with open(schema_file, "w") as f:
                    json.dump(schema, f)

            snapshots_dir = tmpdir_path / "model_guidance_snapshots" / "google"
            snapshots_dir.mkdir(parents=True, exist_ok=True)

            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(days=30)).isoformat().replace("+00:00", "Z")

            snapshot = {
                "record_type": "model_guidance_snapshot",
                "schema_version": "0.x-draft",
                "snapshot_id": "nano_banana__2026-05-09",
                "internal_model_target": "nano_banana_best_available",
                "provider": "google",
                "model_family": "image_generation",
                "provider_surface": "gemini_app",
                "observed_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": expires_at,
                "human_verified": True,
                "current_default_model": "Nano Banana v1",
                "latest_available_model": "Nano Banana v2",
                "best_for_this_task": "Nano Banana v2",
                "feature_required_model": {},
                "version_policy": {
                    "hardcode_in_adapter": False,
                    "adapter_must_read_snapshot": True,
                    "prompt_generation_blocks_if_expired": True,
                    "prompt_generation_blocks_if_unverified": True,
                },
                "sources": [
                    {
                        "source_type": "official_docs",
                        "title": "Test",
                        "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                        "url": "https://example.com",
                    }
                ],
                "capabilities": {},
                "constraints": {},
                "prompting_rules": [],
                "provenance": {
                    "created_by": "test",
                    "created_at": now.isoformat().replace("+00:00", "Z"),
                },
            }

            snapshot_file = snapshots_dir / "2026-05-09T120000Z__nano_banana_best_available.yaml"
            with open(snapshot_file, "w") as f:
                yaml.dump(snapshot, f)

            adapter = MockAdapterDynamicSnapshot(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = MockBrief()

            prompt_record, run_record = adapter.generate(brief, version=1, run_counter=1)

            assert prompt_record["prompt_id"] == "SC0001__t2i-char-c01-test-model-dynamic__v01"
            assert prompt_record["target_models"] == ["test_model_dynamic"]
            assert prompt_record["generation_params"]["model_guidance_mode"] == "dynamic_snapshot"
            assert prompt_record["generation_params"]["resolved_model_name"] == "Nano Banana v2"
            assert prompt_record["generation_params"]["provider"] == "google"

            assert run_record["model"] == "test_model_dynamic"
            assert run_record["status"] == "pending"
