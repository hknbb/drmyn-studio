"""
Tests for A7.2 MidjourneyAdapter model guidance integration.

Validates:
1. INTERNAL_MODEL_TARGET is set to midjourney_image_best_available
2. Dynamic snapshot mode resolves model guidance and populates A6.3 generation_params
3. locked_guide mode remains backward-compatible
4. recommended_model_version is not hardcoded in generation_params
5. A6.4 no-hardcoded-provider-version audit passes for midjourney.py
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.adapters.midjourney import MidjourneyAdapter
from scripts.agents.model_guidance_resolver import ModelGuidanceResolutionError
from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor

REPO_ROOT = Path(__file__).parent.parent.parent


def _make_brief() -> NeutralBrief:
    from scripts.agents.neutral_brief import _safe_subject_label, _planning_aliases_for

    return NeutralBrief(
        scene_id="SC0001",
        element_type="character",
        element_id="C01",
        element_name="Nadia",
        visual_anchors=[
            VisualAnchor(description="Lean silhouette, upright posture.", source_field="char.visual"),
        ],
        negative_constraints=["neon lighting"],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        warnings=[],
        prompt_subject_label=_safe_subject_label("Nadia", "character"),
        planning_aliases=_planning_aliases_for("Nadia", "character"),
    )


def _create_midjourney_snapshot(tmpdir: Path, **overrides) -> Path:
    snapshots_dir = tmpdir / "model_guidance_snapshots" / "midjourney"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    snapshot = {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260509T120000Z_midjourney",
        "internal_model_target": "midjourney_image_best_available",
        "provider": "midjourney",
        "model_family": "image_generation",
        "provider_surface": "web_ui",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "human_verified": True,
        "current_default_model": "V7",
        "latest_available_model": "V8.1",
        "best_for_this_task": "V8.1",
        "feature_required_model": {
            "omni_reference": "V7",
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
                "title": "Midjourney Version Documentation",
                "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                "url": "https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version",
            }
        ],
        "capabilities": {
            "output_type": "image",
            "supports_negative_prompt_via_flag": True,
        },
        "constraints": {
            "word_priority_window": 40,
        },
        "prompting_rules": [
            "Always specify aspect ratio.",
        ],
        "provenance": {
            "created_by": "test",
            "created_at": now.isoformat().replace("+00:00", "Z"),
        },
    }
    snapshot.update(overrides)

    snapshot_file = snapshots_dir / "20260509T120000Z_midjourney_image_best_available.yaml"
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


class TestMidjourneyInternalTarget:
    """Verify INTERNAL_MODEL_TARGET is set correctly."""

    def test_internal_model_target_set(self):
        """MidjourneyAdapter must expose midjourney_image_best_available as target."""
        assert MidjourneyAdapter.INTERNAL_MODEL_TARGET == "midjourney_image_best_available"

    def test_internal_model_target_instance(self, tmp_path):
        adapter = MidjourneyAdapter(tmp_path)
        assert adapter.INTERNAL_MODEL_TARGET == "midjourney_image_best_available"


class TestMidjourneyLockedGuideModeCompat:
    """Verify locked_guide mode (default) is backward-compatible."""

    def test_default_mode_is_locked_guide(self, tmp_path):
        adapter = MidjourneyAdapter(tmp_path)
        assert adapter.model_guidance_mode == "locked_guide"

    def test_locked_guide_generation_params_structure(self, tmp_path):
        adapter = MidjourneyAdapter(tmp_path)
        brief = _make_brief()
        params = adapter._generation_params(brief)

        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_ref"] == "docs/model_guides/midjourney.yaml"
        assert params["adapter_name"] == "midjourney"
        assert "model_guidance_snapshot_ref" not in params
        assert "resolved_model_name" not in params

    def test_no_hardcoded_model_version_in_params(self, tmp_path):
        """recommended_model_version must not be in generation_params."""
        adapter = MidjourneyAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)
        params = record["generation_params"]

        assert "recommended_model_version" not in params

    def test_recommended_ar_preserved(self, tmp_path):
        """recommended_ar (non-version param) must remain in generation_params."""
        adapter = MidjourneyAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)
        params = record["generation_params"]

        assert params["recommended_ar"] == "--ar 16:9"


class TestMidjourneyDynamicSnapshotMode:
    """Test dynamic_snapshot mode with real midjourney snapshot."""

    def test_dynamic_snapshot_resolves_model(self):
        """Dynamic snapshot mode resolves model and populates A6.3 fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_midjourney_snapshot(tmpdir_path)

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            params = adapter._generation_params(brief)

            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert "model_guidance_snapshot_ref" in params
            assert "provider" in params
            assert params["provider"] == "midjourney"
            assert "provider_surface" in params
            assert "resolved_model_name" in params
            assert "resolved_model_role" in params
            assert "guidance_observed_at" in params
            assert "guidance_expires_at" in params

    def test_dynamic_snapshot_resolved_model_not_hardcoded(self):
        """resolved_model_name comes from snapshot, not from adapter source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_midjourney_snapshot(tmpdir_path)

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            params = adapter._generation_params(brief)

            # Value comes from snapshot best_for_this_task: "V8.1"
            assert params["resolved_model_name"] == "V8.1"

    def test_dynamic_snapshot_missing_blocks_generation(self):
        """Missing snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            # No snapshot created

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()

            with pytest.raises(ModelGuidanceResolutionError):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_expired_blocks_generation(self):
        """Expired snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_midjourney_snapshot(
                tmpdir_path,
                expires_at="2020-01-01T00:00:00Z",
            )

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()

            with pytest.raises(ModelGuidanceResolutionError):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_unverified_blocks_generation(self):
        """Unverified snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_midjourney_snapshot(
                tmpdir_path,
                human_verified=False,
            )

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()

            with pytest.raises(ModelGuidanceResolutionError, match="[Vv]erif"):
                adapter._generation_params(brief)

    def test_dynamic_snapshot_generate_produces_valid_record(self):
        """generate() in dynamic mode produces complete prompt_record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_midjourney_snapshot(tmpdir_path)

            adapter = MidjourneyAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            record, run_record = adapter.generate(brief)

            assert record["target_models"] == ["midjourney"]
            assert "prompt_text" in record
            assert "negative_prompt" in record
            params = record["generation_params"]
            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert "resolved_model_name" in params
            assert run_record["model"] == "midjourney"


class TestMidjourneyAuditCompliance:
    """Verify A6.4 audit still passes after A7.2 changes."""

    def test_midjourney_adapter_passes_audit(self):
        """midjourney.py must not contain forbidden provider version literals."""
        from scripts.validators.check_no_hardcoded_model_versions import audit_file

        adapter_path = REPO_ROOT / "scripts" / "agents" / "adapters" / "midjourney.py"
        findings = audit_file(adapter_path)

        assert len(findings) == 0, (
            f"midjourney.py contains forbidden literals: "
            f"{[(f.line_no, f.blocked_literal) for f in findings]}"
        )
