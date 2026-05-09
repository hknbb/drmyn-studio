"""
Tests for A7.3 ChatGPTImageAdapter model guidance integration.

Validates:
1. INTERNAL_MODEL_TARGET is set to chatgpt_image_best_available
2. Dynamic snapshot mode resolves model guidance and populates A6.3 generation_params
3. locked_guide mode remains backward-compatible
4. negative_prompt is always omitted (not supported by ChatGPT Image)
5. constraint_strategy=embedded_positive_constraints is preserved in both modes
6. A6.4 no-hardcoded-provider-version audit passes for chatgpt_image.py
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter
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
        negative_constraints=["neon lighting", "blurred background"],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        warnings=[],
        prompt_subject_label=_safe_subject_label("Nadia", "character"),
        planning_aliases=_planning_aliases_for("Nadia", "character"),
    )


def _create_openai_snapshot(tmpdir: Path, **overrides) -> Path:
    snapshots_dir = tmpdir / "model_guidance_snapshots" / "openai"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    snapshot = {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": "20260509T120000Z_chatgpt_image",
        "internal_model_target": "chatgpt_image_best_available",
        "provider": "openai",
        "model_family": "image_generation",
        "provider_surface": "chatgpt_ui",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "human_verified": True,
        "current_default_model": "test-openai-model-v1",
        "latest_available_model": "test-openai-model-v2",
        "best_for_this_task": "test-openai-model-v2",
        "feature_required_model": {
            "natural_language_revision": "test-openai-model-v2",
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
                "title": "OpenAI Image Generation API Guide",
                "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                "url": "https://developers.openai.com/api/docs/guides/image-generation",
            }
        ],
        "capabilities": {
            "output_type": "image",
            "supports_negative_prompt": False,
            "constraint_strategy": "embedded_positive_constraints",
        },
        "constraints": {
            "negative_prompt_not_available": True,
        },
        "prompting_rules": [
            "Use full sentences. Embed constraints via Avoid clause.",
        ],
        "provenance": {
            "created_by": "test",
            "created_at": now.isoformat().replace("+00:00", "Z"),
        },
    }
    snapshot.update(overrides)

    snapshot_file = snapshots_dir / "20260509T120000Z_chatgpt_image_best_available.yaml"
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


class TestChatGPTImageInternalTarget:
    """Verify INTERNAL_MODEL_TARGET is set correctly."""

    def test_internal_model_target_class_attr(self):
        assert ChatGPTImageAdapter.INTERNAL_MODEL_TARGET == "chatgpt_image_best_available"

    def test_internal_model_target_instance(self, tmp_path):
        adapter = ChatGPTImageAdapter(tmp_path)
        assert adapter.INTERNAL_MODEL_TARGET == "chatgpt_image_best_available"


class TestChatGPTImageLockedGuideModeCompat:
    """Verify locked_guide mode (default) is backward-compatible."""

    def test_default_mode_is_locked_guide(self, tmp_path):
        adapter = ChatGPTImageAdapter(tmp_path)
        assert adapter.model_guidance_mode == "locked_guide"

    def test_locked_guide_generation_params_structure(self, tmp_path):
        adapter = ChatGPTImageAdapter(tmp_path)
        brief = _make_brief()
        params = adapter._generation_params(brief)

        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_ref"] == "docs/model_guides/chatgpt_image.yaml"
        assert params["adapter_name"] == "chatgpt_image"
        assert "model_guidance_snapshot_ref" not in params
        assert "resolved_model_name" not in params

    def test_constraint_strategy_preserved_locked_guide(self, tmp_path):
        """constraint_strategy must be embedded_positive_constraints in locked_guide mode."""
        adapter = ChatGPTImageAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)
        params = record["generation_params"]

        assert params["constraint_strategy"] == "embedded_positive_constraints"

    def test_no_negative_prompt_locked_guide(self, tmp_path):
        """negative_prompt must be absent — ChatGPT Image does not support it."""
        adapter = ChatGPTImageAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)

        assert "negative_prompt" not in record

    def test_recommended_quality_preserved(self, tmp_path):
        adapter = ChatGPTImageAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)

        assert record["generation_params"]["recommended_quality"] == "medium"

    def test_prompt_structure_preserved(self, tmp_path):
        adapter = ChatGPTImageAdapter(tmp_path)
        brief = _make_brief()
        record, _ = adapter.generate(brief)

        assert record["generation_params"]["prompt_structure"] == "scene→subject→details→constraints"


class TestChatGPTImageDynamicSnapshotMode:
    """Test dynamic_snapshot mode with OpenAI snapshot."""

    def test_dynamic_snapshot_resolves_model(self):
        """Dynamic snapshot mode resolves model and populates A6.3 fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_openai_snapshot(tmpdir_path)

            adapter = ChatGPTImageAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            params = adapter._generation_params(brief)

            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert "model_guidance_snapshot_ref" in params
            assert params["provider"] == "openai"
            assert params["provider_surface"] == "chatgpt_ui"
            assert "resolved_model_name" in params
            assert "resolved_model_role" in params
            assert "guidance_observed_at" in params
            assert "guidance_expires_at" in params

    def test_dynamic_snapshot_resolved_model_from_snapshot(self):
        """resolved_model_name comes from snapshot best_for_this_task, not adapter source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_openai_snapshot(tmpdir_path)

            adapter = ChatGPTImageAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            params = adapter._generation_params(brief)

            assert params["resolved_model_name"] == "test-openai-model-v2"

    def test_dynamic_snapshot_no_negative_prompt(self):
        """negative_prompt must remain absent in dynamic_snapshot mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_openai_snapshot(tmpdir_path)

            adapter = ChatGPTImageAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            record, _ = adapter.generate(brief)

            assert "negative_prompt" not in record

    def test_dynamic_snapshot_constraint_strategy_preserved(self):
        """constraint_strategy must remain embedded_positive_constraints in dynamic mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            _create_openai_snapshot(tmpdir_path)

            adapter = ChatGPTImageAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            record, _ = adapter.generate(brief)

            assert record["generation_params"]["constraint_strategy"] == "embedded_positive_constraints"

    def test_dynamic_snapshot_missing_blocks_generation(self):
        """Missing snapshot must raise ModelGuidanceResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _copy_schema(tmpdir_path)
            # No snapshot created

            adapter = ChatGPTImageAdapter(
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
            _create_openai_snapshot(
                tmpdir_path,
                expires_at="2020-01-01T00:00:00Z",
            )

            adapter = ChatGPTImageAdapter(
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
            _create_openai_snapshot(
                tmpdir_path,
                human_verified=False,
            )

            adapter = ChatGPTImageAdapter(
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
            _create_openai_snapshot(tmpdir_path)

            adapter = ChatGPTImageAdapter(
                tmpdir_path,
                model_guidance_mode="dynamic_snapshot",
            )
            brief = _make_brief()
            record, run_record = adapter.generate(brief)

            assert record["target_models"] == ["chatgpt_image"]
            assert "prompt_text" in record
            assert "negative_prompt" not in record
            params = record["generation_params"]
            assert params["model_guidance_mode"] == "dynamic_snapshot"
            assert params["constraint_strategy"] == "embedded_positive_constraints"
            assert "resolved_model_name" in params
            assert run_record["model"] == "chatgpt_image"


class TestChatGPTImageAuditCompliance:
    """Verify A6.4 audit still passes after A7.3 changes."""

    def test_chatgpt_image_adapter_passes_audit(self):
        """chatgpt_image.py must not contain forbidden provider version literals."""
        from scripts.validators.check_no_hardcoded_model_versions import audit_file

        adapter_path = REPO_ROOT / "scripts" / "agents" / "adapters" / "chatgpt_image.py"
        findings = audit_file(adapter_path)

        assert len(findings) == 0, (
            f"chatgpt_image.py contains forbidden literals: "
            f"{[(f.line_no, f.blocked_literal) for f in findings]}"
        )
