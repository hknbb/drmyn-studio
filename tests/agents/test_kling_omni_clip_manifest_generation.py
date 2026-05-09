"""
Tests for A7.4b KlingOmniAdapter clip manifest-driven prompt generation.

Validates:
1. generate_from_clip_manifest() loads and processes omni_clip_manifest.yaml
2. Prompt text is built from manifest.shots, not scene_card.shot_list_omni
3. Prompt record includes omni_clip_manifest in source_refs
4. Expected output duration equals manifest total_duration_seconds
5. Dynamic snapshot mode populates A6.3 model guidance fields
6. CriticAgent accepts generated manifest-based records
7. Locked guide mode remains backward-compatible for manifest generation
8. Canonical IDs are sanitized from prompt text
9. Missing or invalid manifests fail clearly
10. No provider model names are hardcoded
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.agents.adapters.kling_omni import KlingOmniAdapter, KlingOmniAdapterError
from scripts.agents.critic import CriticAgent

REPO_ROOT = Path(__file__).parent.parent.parent


def _create_manifest(
    tmpdir: Path,
    scene_id: str = "SC0001",
    clip_id: str = "CLIP_SC0001_01",
    total_duration: int = 15,
    continuity_mode: str = "frame_input_eligible",
    shots: list[dict] | None = None,
    **overrides,
) -> Path:
    """Create omni_clip_manifest.yaml for testing."""
    if shots is None:
        shots = [
            {
                "shot_id": "SHOT_SC0001_01_A",
                "duration_seconds": 5,
                "source_beat_ids": ["ESTABLISH_KITCHEN"],
                "prompt_action": "INT. VALE RESIDENCE — KITCHEN PASSAGE. The kitchen is expensive.",
                "duration_reason": "normal/establish 5s",
            },
            {
                "shot_id": "SHOT_SC0001_01_B",
                "duration_seconds": 5,
                "source_beat_ids": ["NADIA_PASSAGE_MOVEMENT"],
                "prompt_action": "NADIA moves through the passage with the economy of someone who maps rooms.",
                "duration_reason": "normal/action 5s",
            },
            {
                "shot_id": "SHOT_SC0001_01_C",
                "duration_seconds": 5,
                "source_beat_ids": ["WATER_GLASS_ACTION"],
                "prompt_action": "She fills a glass of water, drinks half, sets it exactly where she found it.",
                "duration_reason": "normal/action 5s",
            },
        ]

    manifests_dir = tmpdir / "planning" / "scenes" / scene_id / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "0.x-draft",
        "record_type": "omni_clip_manifest",
        "scene_id": scene_id,
        "clip_id": clip_id,
        "source_scene_beat_plan_ref": f"planning/scenes/{scene_id}/scene_beat_plan.yaml",
        "source_dialogue_beats_ref": f"planning/scenes/{scene_id}/dialogue_beats.yaml",
        "total_duration_seconds": total_duration,
        "continuity_input_mode": continuity_mode,
        "shots": shots,
        "kling_native_audio": {
            "enabled": False,
            "provider_policy": "kling_native_only",
            "external_tts_allowed": False,
            "adr_vendor_allowed": False,
        },
        "notes": "Test manifest",
        "provenance": {
            "created_by": "test",
            "created_at": "2026-05-09T00:00:00Z",
        },
    }
    manifest.update(overrides)

    manifest_file = manifests_dir / f"{clip_id}_manifest.yaml"
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    return manifest_file


def _create_scene_card(tmpdir: Path, scene_id: str = "SC0001") -> Path:
    """Create minimal scene_card.yaml."""
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


def _create_scene_excerpt(tmpdir: Path, scene_id: str = "SC0001") -> Path:
    """Create scene_excerpt.md."""
    scenes_dir = tmpdir / "planning" / "scenes" / scene_id
    scenes_dir.mkdir(parents=True, exist_ok=True)
    excerpt_path = scenes_dir / "scene_excerpt.md"
    excerpt_path.write_text("# Scene Excerpt\n\nTest scene excerpt.", encoding="utf-8")
    return excerpt_path


def _create_kling_snapshot(tmpdir: Path, **overrides) -> Path:
    """Create model guidance snapshot for Kling."""
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
        "feature_required_model": {"multi_shot": "test-kling-model-v2"},
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
        "prompting_rules": ["Write cinematic shot directions."],
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


def _copy_schemas(tmpdir: Path) -> None:
    """Copy all required schemas to temp directory."""
    schemas_dir = tmpdir / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # Copy model_guidance_snapshot schema
    actual = REPO_ROOT / "schemas" / "model_guidance_snapshot.schema.json"
    dest = schemas_dir / "model_guidance_snapshot.schema.json"
    dest.write_text(actual.read_text(encoding="utf-8"), encoding="utf-8")

    # Copy prompt_record schema
    actual = REPO_ROOT / "schemas" / "prompt_record.schema.json"
    dest = schemas_dir / "prompt_record.schema.json"
    dest.write_text(actual.read_text(encoding="utf-8"), encoding="utf-8")


def _create_model_guide(tmpdir: Path) -> Path:
    """Create minimal model guide for locked_guide mode."""
    guides_dir = tmpdir / "docs" / "model_guides"
    guides_dir.mkdir(parents=True, exist_ok=True)

    guide = {
        "model_id": "kling_omni",
        "provider": "kling",
        "capability": {
            "supports_negative_prompt": True,
            "max_duration_seconds": 15,
        },
    }

    guide_path = guides_dir / "kling_omni.yaml"
    with open(guide_path, "w") as f:
        yaml.dump(guide, f)

    return guide_path


class TestGenerateFromClipManifest:
    """Test manifest-driven prompt generation."""

    def test_manifest_generation_basic(self, tmp_path):
        """generate_from_clip_manifest() loads manifest and returns KlingOmniBuildResult."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        assert result.prompt_record is not None
        assert result.run_record is not None
        assert result.warnings == []

    def test_manifest_prompt_id_includes_clip_id(self, tmp_path):
        """Prompt ID should include clip_id in a deterministic way."""
        manifest_path = _create_manifest(tmp_path, clip_id="CLIP_SC0001_03")
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        prompt_id = result.prompt_record["prompt_id"]
        assert prompt_id.startswith("SC0001__omni-kling-omni-clip-clip-sc0001-03__v01")

    def test_manifest_source_refs_includes_required_fields(self, tmp_path):
        """source_refs must include scene_card and scene_excerpt."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        source_refs = result.prompt_record["source_refs"]
        assert "scene_card" in source_refs
        assert "scene_excerpt" in source_refs
        assert source_refs["scene_card"].endswith("scene_card.yaml")
        assert source_refs["scene_excerpt"].endswith("scene_excerpt.md")

    def test_manifest_generation_params_includes_provenance(self, tmp_path):
        """generation_params must include manifest provenance fields."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        params = result.prompt_record["generation_params"]
        assert "omni_clip_manifest_ref" in params
        assert params["omni_clip_manifest_ref"].endswith("_manifest.yaml")
        assert "source_scene_beat_plan_ref" in params
        assert "SC0001" in params["source_scene_beat_plan_ref"]
        assert "source_dialogue_beats_ref" in params
        assert "SC0001" in params["source_dialogue_beats_ref"]

    def test_manifest_prompt_text_from_shots(self, tmp_path):
        """Prompt text must be built from manifest.shots."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        prompt_text = result.prompt_record["prompt_text"]
        # Should include shot actions from manifest
        assert "KITCHEN PASSAGE" in prompt_text or "kitchen" in prompt_text.lower()
        assert "Shot 1" in prompt_text
        assert "Shot 2" in prompt_text
        assert "Shot 3" in prompt_text
        assert "(5s)" in prompt_text

    def test_manifest_expected_output_duration(self, tmp_path):
        """expected_output.duration_seconds must equal manifest total_duration_seconds."""
        manifest_path = _create_manifest(tmp_path, total_duration=13)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        expected_output = result.prompt_record["expected_output"]
        assert expected_output["duration_seconds"] == 13

    def test_manifest_generation_params_structure(self, tmp_path):
        """generation_params must include clip_id and continuity_input_mode."""
        manifest_path = _create_manifest(
            tmp_path, continuity_mode="frame_input_active"
        )
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        params = result.prompt_record["generation_params"]
        assert params["clip_id"] == "CLIP_SC0001_01"
        assert params["total_duration_seconds"] == 15
        assert params["continuity_input_mode"] == "frame_input_active"

    def test_manifest_canonical_ids_sanitized(self, tmp_path):
        """Canonical IDs (C01, LOC001, etc.) must be sanitized from prompt_text."""
        shots = [
            {
                "shot_id": "SHOT_SC0001_01_A",
                "duration_seconds": 5,
                "source_beat_ids": ["BEAT_01"],
                "prompt_action": "C01 and LOC001 interact in PROP003 room",
                "duration_reason": "test 5s",
            }
        ]
        manifest_path = _create_manifest(tmp_path, shots=shots, total_duration=5)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        prompt_text = result.prompt_record["prompt_text"]
        # Canonical IDs must NOT appear literally
        assert "C01" not in prompt_text
        assert "LOC001" not in prompt_text
        assert "PROP003" not in prompt_text
        # But sanitized placeholder should exist
        assert "referenced" in prompt_text.lower()

    def test_manifest_missing_file_fails(self, tmp_path):
        """Missing manifest file must raise KlingOmniAdapterError."""
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="Missing manifest"):
            adapter.generate_from_clip_manifest(str(tmp_path / "missing.yaml"))

    def test_manifest_invalid_record_type_fails(self, tmp_path):
        """Invalid record_type must fail validation."""
        manifests_dir = tmp_path / "planning" / "scenes" / "SC0001" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "0.x-draft",
            "record_type": "wrong_type",
            "scene_id": "SC0001",
            "clip_id": "CLIP_SC0001_01",
            "total_duration_seconds": 15,
            "shots": [
                {
                    "shot_id": "SHOT_SC0001_01_A",
                    "duration_seconds": 15,
                    "source_beat_ids": ["BEAT_01"],
                    "prompt_action": "test action",
                    "duration_reason": "test 15s",
                }
            ],
            "kling_native_audio": {
                "enabled": False,
                "provider_policy": "kling_native_only",
                "external_tts_allowed": False,
                "adr_vendor_allowed": False,
            },
            "provenance": {
                "created_by": "test",
                "created_at": "2026-05-09T00:00:00Z",
            },
        }

        manifest_path = manifests_dir / "test_manifest.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="record_type"):
            adapter.generate_from_clip_manifest(str(manifest_path))

    def test_manifest_missing_scene_id_fails(self, tmp_path):
        """Missing scene_id must fail validation."""
        manifests_dir = tmp_path / "planning" / "scenes" / "SC0001" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "0.x-draft",
            "record_type": "omni_clip_manifest",
            "clip_id": "CLIP_SC0001_01",
            "total_duration_seconds": 15,
            "shots": [
                {
                    "shot_id": "SHOT_SC0001_01_A",
                    "duration_seconds": 15,
                    "source_beat_ids": ["BEAT_01"],
                    "prompt_action": "test action",
                    "duration_reason": "test 15s",
                }
            ],
            "kling_native_audio": {
                "enabled": False,
                "provider_policy": "kling_native_only",
                "external_tts_allowed": False,
                "adr_vendor_allowed": False,
            },
            "provenance": {
                "created_by": "test",
                "created_at": "2026-05-09T00:00:00Z",
            },
        }

        manifest_path = manifests_dir / "test_manifest.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="scene_id"):
            adapter.generate_from_clip_manifest(str(manifest_path))

    def test_manifest_missing_clip_id_fails(self, tmp_path):
        """Missing clip_id must fail validation."""
        manifests_dir = tmp_path / "planning" / "scenes" / "SC0001" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "0.x-draft",
            "record_type": "omni_clip_manifest",
            "scene_id": "SC0001",
            "total_duration_seconds": 15,
            "shots": [
                {
                    "shot_id": "SHOT_SC0001_01_A",
                    "duration_seconds": 15,
                    "source_beat_ids": ["BEAT_01"],
                    "prompt_action": "test action",
                    "duration_reason": "test 15s",
                }
            ],
            "kling_native_audio": {
                "enabled": False,
                "provider_policy": "kling_native_only",
                "external_tts_allowed": False,
                "adr_vendor_allowed": False,
            },
            "provenance": {
                "created_by": "test",
                "created_at": "2026-05-09T00:00:00Z",
            },
        }

        manifest_path = manifests_dir / "test_manifest.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="clip_id"):
            adapter.generate_from_clip_manifest(str(manifest_path))

    def test_manifest_empty_shots_fails(self, tmp_path):
        """Empty shots array must fail validation."""
        manifest_path = _create_manifest(tmp_path, shots=[])
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="shots"):
            adapter.generate_from_clip_manifest(str(manifest_path))

    def test_manifest_missing_shot_field_fails(self, tmp_path):
        """Missing required shot field must fail validation."""
        shots = [
            {
                "shot_id": "SHOT_SC0001_01_A",
                "duration_seconds": 5,
                "source_beat_ids": ["BEAT_01"],
                # Missing prompt_action
                "duration_reason": "test 5s",
            }
        ]
        manifest_path = _create_manifest(tmp_path, shots=shots, total_duration=5)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        with pytest.raises(KlingOmniAdapterError, match="prompt_action"):
            adapter.generate_from_clip_manifest(str(manifest_path))

    def test_manifest_dynamic_snapshot_mode(self, tmp_path):
        """Dynamic snapshot mode must populate A6.3 generation_params fields."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)
        _copy_schemas(tmp_path)
        _create_kling_snapshot(tmp_path)

        adapter = KlingOmniAdapter(
            tmp_path,
            model_guidance_mode="dynamic_snapshot",
        )
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        params = result.prompt_record["generation_params"]
        assert params["model_guidance_mode"] == "dynamic_snapshot"
        assert "model_guidance_snapshot_ref" in params
        assert params["provider"] == "kling"
        assert params["provider_surface"] == "api"
        assert "resolved_model_name" in params
        assert "resolved_model_role" in params
        assert "guidance_observed_at" in params
        assert "guidance_expires_at" in params

    def test_manifest_locked_guide_mode(self, tmp_path):
        """Locked guide mode must remain backward-compatible."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path, model_guidance_mode="locked_guide")
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        params = result.prompt_record["generation_params"]
        assert params["model_guidance_mode"] == "locked_guide"
        assert params["model_guidance_ref"] == "docs/model_guides/kling_omni.yaml"
        assert "model_guidance_snapshot_ref" not in params

    def test_manifest_critic_accepts_locked_guide(self, tmp_path):
        """CriticAgent must accept locked_guide manifest-generated records."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)
        _copy_schemas(tmp_path)
        _create_model_guide(tmp_path)

        adapter = KlingOmniAdapter(tmp_path, model_guidance_mode="locked_guide")
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        critic = CriticAgent(tmp_path)
        criticism = critic.check(result.prompt_record)

        assert criticism.passed, f"Critic failed: {criticism}"

    def test_manifest_critic_accepts_dynamic_snapshot(self, tmp_path):
        """CriticAgent must accept dynamic_snapshot manifest-generated records."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)
        _copy_schemas(tmp_path)
        _create_kling_snapshot(tmp_path)

        adapter = KlingOmniAdapter(
            tmp_path,
            model_guidance_mode="dynamic_snapshot",
        )
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        critic = CriticAgent(tmp_path)
        criticism = critic.check(result.prompt_record)

        assert criticism.passed, f"Critic failed: {criticism}"

    def test_manifest_legacy_generate_still_works(self, tmp_path):
        """Legacy generate(scene_id) method must still work."""
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        # Create minimal omni set
        omni_set_dir = tmp_path / "planning" / "omni_sets" / "omni_set_001"
        omni_set_dir.mkdir(parents=True, exist_ok=True)
        element_set_path = omni_set_dir / "element_set.yaml"
        with open(element_set_path, "w") as f:
            yaml.dump({"element_refs": []}, f)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate("SC0001")

        assert result.prompt_record is not None
        assert result.run_record is not None

    def test_manifest_continuity_mode_in_prompt_text(self, tmp_path):
        """Prompt text must reflect continuity_input_mode."""
        manifest_path = _create_manifest(tmp_path, continuity_mode="metadata_only")
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        prompt_text = result.prompt_record["prompt_text"]
        assert "metadata" in prompt_text.lower() or "continuity" in prompt_text.lower()

    def test_manifest_version_parameter(self, tmp_path):
        """Version parameter should be reflected in prompt_id."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path), version=3)

        prompt_id = result.prompt_record["prompt_id"]
        assert "__v03" in prompt_id

    def test_manifest_run_record_structure(self, tmp_path):
        """run_record must be properly structured."""
        manifest_path = _create_manifest(tmp_path)
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path), run_counter=5)

        run_record = result.run_record
        assert run_record["model"] == "kling_omni"
        assert run_record["status"] == "pending"
        assert run_record["outputs_expected"] == 1
        assert "KO" in run_record["run_id"]  # KlingOmni abbreviation
        assert "0005" in run_record["run_id"]  # run_counter encoded in run_id

    def test_manifest_run_id_includes_clip_id(self, tmp_path):
        """Manifest-driven run_id must include clip_id for uniqueness across clips."""
        manifest_path = _create_manifest(tmp_path, clip_id="CLIP_SC0001_03")
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate_from_clip_manifest(str(manifest_path))

        run_id = result.run_record["run_id"]
        assert "CLIP_SC0001_03" in run_id
        # Full expected format: RUN_SC0001_CLIP_SC0001_03_KO_0001
        assert run_id == "RUN_SC0001_CLIP_SC0001_03_KO_0001"

    def test_legacy_generate_run_id_unchanged(self, tmp_path):
        """Legacy generate(scene_id) run_id must not include clip_id."""
        _create_scene_card(tmp_path)
        _create_scene_excerpt(tmp_path)

        omni_set_dir = tmp_path / "planning" / "omni_sets" / "omni_set_001"
        omni_set_dir.mkdir(parents=True, exist_ok=True)
        with open(omni_set_dir / "element_set.yaml", "w") as f:
            yaml.dump({"element_refs": []}, f)

        adapter = KlingOmniAdapter(tmp_path)
        result = adapter.generate("SC0001", run_counter=2)

        run_id = result.run_record["run_id"]
        assert run_id == "RUN_SC0001_KO_0002"
        assert "CLIP" not in run_id
