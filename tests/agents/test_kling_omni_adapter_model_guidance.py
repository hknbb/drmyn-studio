"""
Tests for A7.4a KlingOmniAdapter model guidance integration.

Validates:
1. INTERNAL_MODEL_TARGET is set to kling_omni_video_best_available
2. Dynamic snapshot mode resolves model guidance and populates A6.3 generation_params
3. locked_guide mode remains backward-compatible
4. A6.4 no-hardcoded-provider-version audit passes for kling_omni.py
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.adapters.kling_omni import KlingOmniAdapter, KlingOmniAdapterError
from scripts.agents.model_guidance_resolver import ModelGuidanceResolutionError

REPO_ROOT = Path(__file__).parent.parent.parent


def _create_minimal_scene(tmpdir: Path, scene_id: str = "SC0001") -> Path:
    """Create minimal scene_card.yaml for testing."""
    scenes_dir = tmpdir / "planning" / "scenes" / scene_id
    scenes_dir.mkdir(parents=True, exist_ok=True)

    scene_card = {
        "title": "Test Scene",
        "purpose": "Test purposes",
        "shot_list_omni": [
            {
                "duration_seconds": 5,
                "subject": "Approved subject",
                "framing": "source-grounded framing",
            }
        ],
        "omni_set_ref": "planning/omni_sets/omni_set_001",
    }

    scene_card_path = scenes_dir / "scene_card.yaml"
    with open(scene_card_path, "w") as f:
        yaml.dump(scene_card, f)

    return scene_card_path


def _create_kling_snapshot(tmpdir: Path, **overrides) -> Path:
    snapshots_dir = tmpdir / "model_guidance_snapshots" / "kling"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    snapshot = {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260509T120000Z_kling_omni",
        "internal_model_target": "kling_omni_video_best_available",
        "provider": "kling",
        "model_family": "video_generation",
        "provider_surface": "api",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "human_verified": True,
        "current_default_model": "test-kling-model-v1",
        "latest_available_model": "test-kling-model-v2",
        "best_for_this_task": "test-kling-model-v2",
        "feature_required_model": {
            "multi_shot": "test-kling-model-v2",
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
                "title": "Kling API Documentation",
                "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                "url": "https://kling.ai/docs/api/video-generation",
            }
        ],
        "capabilities": {
            "output_type": "video",
            "supports_negative_prompt": True,
            "max_duration_seconds": 15,
        },
        "constraints": {
            "min_duration_seconds": 3,
            "max_shots_per_generation": 6,
        },
        "prompting_rules": [
            "Write cinematic shot directions.",
        ],
        "provenance": {
            "created_by": "test",
            "created_at": now.isoformat().replace("+00:00", "Z"),
        },
    }
    snapshot.update(overrides)

    snapshot_file = snapshots_dir / "20260509T120000Z_kling_omni_video_best_available.yaml"
    with open(snapshot_file, "w") as f:
        yaml.dump(snapshot, f)

    return snapshot_file


def _copy_schema(tmpdir: Path) -> Path:
    schemas_dir = tmpdir / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    actual = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"
    dest = schemas_dir / "model_guidance_snapshot.schema.json"
    dest.write_text(actual.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def _create_omni_set(tmpdir: Path) -> Path:
    """Create minimal omni_set directory with element_set.yaml."""
    omni_set_dir = tmpdir / "planning" / "omni_sets" / "omni_set_001"
    omni_set_dir.mkdir(parents=True, exist_ok=True)

    element_set = {
        "element_refs": [],
    }

    element_set_path = omni_set_dir / "element_set.yaml"
    with open(element_set_path, "w") as f:
        yaml.dump(element_set, f)

    return element_set_path


class TestKlingOmniInternalTarget:
    """Verify INTERNAL_MODEL_TARGET is set correctly."""

    def test_internal_model_target_class_attr(self):
        assert KlingOmniAdapter.INTERNAL_MODEL_TARGET == "kling_omni_video_best_available"

    def test_internal_model_target_instance(self, tmp_path):
        adapter = KlingOmniAdapter(tmp_path)
        assert adapter.INTERNAL_MODEL_TARGET == "kling_omni_video_best_available"


class TestKlingOmniLockedGuideModeCompat:
    """Verify locked_guide mode (default) is backward-compatible."""

    def test_default_mode_is_locked_guide(self, tmp_path):
        adapter = KlingOmniAdapter(tmp_path)
        assert adapter.model_guidance_mode == "locked_guide"

    def test_locked_guide_generation_params_structure(self, tmp_path):
        """Locked guide mode should populate legacy fields."""
        _create_minimal_scene(tmp_path)
        _create_omni_set(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate("SC0001")

        params = result.prompt_record["generation_params"]
        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_ref"] == "docs/model_guides/kling_omni.yaml"
        assert params["adapter_name"] == "kling_omni"
        assert "model_guidance_snapshot_ref" not in params
        assert "resolved_model_name" not in params

    def test_locked_guide_preserves_existing_params(self, tmp_path):
        """Locked guide should preserve max_duration, cfg_scale, ar, etc."""
        _create_minimal_scene(tmp_path)
        _create_omni_set(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate("SC0001")

        params = result.prompt_record["generation_params"]
        assert "max_duration_seconds" in params
        assert "recommended_cfg_scale" in params
        assert "recommended_ar" in params
        assert params["recommended_ar"] == "16:9"


class TestKlingOmniDynamicSnapshotMode:
    """Test dynamic_snapshot mode with Kling snapshot."""

    def test_dynamic_snapshot_resolves_model(self):
        """Dynamic snapshot mode resolves model and populates A6.3 fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            _create_kling_snapshot(tmpdir_path)

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            result = adapter.generate("SC0001")
            params = result.prompt_record["generation_params"]

            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert "model_guidance_snapshot_ref" in params
            assert params["provider"] == "kling"
            assert params["provider_surface"] == "api"
            assert "resolved_model_name" in params
            assert "resolved_model_role" in params
            assert "guidance_observed_at" in params
            assert "guidance_expires_at" in params

    def test_dynamic_snapshot_resolved_model_from_snapshot(self):
        """resolved_model_name comes from snapshot best_for_this_task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            _create_kling_snapshot(tmpdir_path)

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            result = adapter.generate("SC0001")
            params = result.prompt_record["generation_params"]

            assert params["resolved_model_name"] == "test-kling-model-v2"

    def test_dynamic_snapshot_missing_blocks_generation(self):
        """Missing snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            # No snapshot created

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )

            with pytest.raises(ModelGuidanceResolutionError):
                adapter.generate("SC0001")

    def test_dynamic_snapshot_expired_blocks_generation(self):
        """Expired snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            _create_kling_snapshot(
                tmpdir_path,
                expires_at="2020-01-01T00:00:00Z",
            )

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )

            with pytest.raises(ModelGuidanceResolutionError):
                adapter.generate("SC0001")

    def test_dynamic_snapshot_unverified_blocks_generation(self):
        """Unverified snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            _create_kling_snapshot(
                tmpdir_path,
                human_verified=False,
            )

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )

            with pytest.raises(ModelGuidanceResolutionError, match="[Vv]erif"):
                adapter.generate("SC0001")

    def test_dynamic_snapshot_generates_valid_record(self):
        """generate() in dynamic mode produces complete prompt_record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _create_minimal_scene(tmpdir_path)
            _create_omni_set(tmpdir_path)
            _copy_schema(tmpdir_path)
            _create_kling_snapshot(tmpdir_path)

            adapter = KlingOmniAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            result = adapter.generate("SC0001")

            assert result.prompt_record["target_models"] == ["kling_omni"]
            assert "prompt_text" in result.prompt_record
            assert "negative_prompt" in result.prompt_record
            params = result.prompt_record["generation_params"]
            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert "resolved_model_name" in params
            assert result.run_record["model"] == "kling_omni"


class TestKlingOmniAuditCompliance:
    """Verify A6.4 audit still passes after A7.4a changes."""

    def test_kling_omni_adapter_passes_audit(self):
        """kling_omni.py must not contain forbidden provider version literals."""
        from scripts.validators.check_no_hardcoded_model_versions import audit_file

        adapter_path = REPO_ROOT / "scripts" / "agents" / "adapters" / "kling_omni.py"
        findings = audit_file(adapter_path)

        assert len(findings) == 0, (
            f"kling_omni.py contains forbidden literals: "
            f"{[(f.line_no, f.blocked_literal) for f in findings]}"
        )
