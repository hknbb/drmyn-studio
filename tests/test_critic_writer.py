"""
tests/test_critic_writer.py — Batch 5

Tests for CriticAgent v1 and PromptWriter.
- CriticAgent hard checks: schema, prompt_id, lifecycle, source_refs,
  canonical IDs, target_models, model_guidance_ref, negative_prompt rule
- CriticAgent soft checks: UNRESOLVED markers
- PromptWriter: file paths, YAML content, CSV rows, library updates
- WriterLifecycleError on non-draft records
- CriticResult + PromptWriter integration
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.critic import CriticAgent, CriticResult  # noqa: E402
from scripts.agents.writer import PromptWriter, WriteResult, WriterLifecycleError  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_valid_record(
    *,
    scene_id: str = "SC0003",
    prompt_id: str = "SC0003__t2i-char-c01-midjourney__v01",
    prompt_text: str = "Nadia Vale, lean upright silhouette, muted domestic neutrals",
    negative_prompt: str | None = "neon cyberpunk, teal-orange grading",
    target_models: list | None = None,
    lifecycle_stage: str = "draft",
    prompt_type: str = "t2i_character_element",
    model_guidance_ref: str = "docs/model_guides/midjourney.yaml",
    model_guidance_mode: str = "locked_guide",
    model_guidance_snapshot: str | None = None,
    extra_generation_params: dict | None = None,
) -> dict:
    params: dict = {
        "model_guidance_mode": model_guidance_mode,
        "model_guidance_ref": model_guidance_ref,
        "adapter_name": (target_models or ["midjourney"])[0],
    }
    if model_guidance_snapshot:
        params["model_guidance_snapshot"] = model_guidance_snapshot
    if extra_generation_params:
        params.update(extra_generation_params)

    record: dict = {
        "prompt_id": prompt_id,
        "scene_id": scene_id,
        "prompt_type": prompt_type,
        "lifecycle_stage": lifecycle_stage,
        "target_models": target_models or ["midjourney"],
        "source_refs": {
            "scene_card": f"planning/scenes/{scene_id}/scene_card.yaml",
            "scene_excerpt": f"planning/scenes/{scene_id}/scene_excerpt.md",
            "character_refs": ["C01"],
        },
        "prompt_text": prompt_text,
        "generation_params": params,
        "expected_output": {"asset_type": "image_set", "variation_count": 4},
        "status": "active",
        "canon_lock": False,
    }

    if negative_prompt is not None:
        record["negative_prompt"] = negative_prompt

    return record


def _make_valid_run_record(
    *,
    run_id: str = "RUN_SC0003_MJ_0001",
    prompt_id: str = "SC0003__t2i-char-c01-midjourney__v01",
    model: str = "midjourney",
    run_at: str = "2026-04-30T12:00:00Z",
) -> dict:
    return {
        "run_id": run_id,
        "prompt_id": prompt_id,
        "model": model,
        "run_at": run_at,
        "outputs_expected": 4,
        "cost": {"unit": "credits", "value": 1},
        "status": "pending",
    }


# ---------------------------------------------------------------------------
# CriticAgent — hard checks
# ---------------------------------------------------------------------------


def test_critic_valid_midjourney_record_passes() -> None:
    """A well-formed Midjourney adapter record passes all hard checks."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record()
    result = critic.check(record)
    assert result.passed, f"Expected pass: {result.hard_errors}"


def test_critic_valid_chatgpt_image_record_passes() -> None:
    """ChatGPT Image record with constraint_strategy and no negative_prompt passes."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        prompt_id="SC0003__t2i-char-c01-chatgpt-image__v01",
        target_models=["chatgpt_image"],
        model_guidance_ref="docs/model_guides/chatgpt_image.yaml",
        negative_prompt=None,
        extra_generation_params={
            "constraint_strategy": "embedded_positive_constraints"
        },
    )
    result = critic.check(record)
    assert result.passed, f"Expected pass: {result.hard_errors}"


def test_critic_non_draft_lifecycle_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(lifecycle_stage="review")
    result = critic.check(record)
    assert not result.passed
    assert any("lifecycle_stage" in e for e in result.hard_errors)


def test_critic_invalid_prompt_id_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(prompt_id="INVALID__prompt__v01")
    result = critic.check(record)
    assert not result.passed
    assert any("prompt_id" in e for e in result.hard_errors)


def test_critic_empty_scene_card_ref_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record()
    record["source_refs"]["scene_card"] = ""
    result = critic.check(record)
    assert not result.passed
    assert any("scene_card" in e for e in result.hard_errors)


def test_critic_canonical_id_c01_in_prompt_text_fails() -> None:
    """C01 appearing literally in prompt_text should be flagged."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        prompt_text="Reference image of C01 in a domestic setting."
    )
    result = critic.check(record)
    assert not result.passed
    assert any("C01" in e for e in result.hard_errors)


def test_critic_canonical_id_loc001_in_prompt_text_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        prompt_text="Set in LOC001 with pale stone walls."
    )
    result = critic.check(record)
    assert not result.passed
    assert any("LOC001" in e for e in result.hard_errors)


def test_critic_multiple_target_models_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(target_models=["midjourney", "chatgpt_image"])
    result = critic.check(record)
    assert not result.passed
    assert any("target_models" in e for e in result.hard_errors)


def test_critic_missing_model_guidance_ref_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record()
    del record["generation_params"]["model_guidance_ref"]
    result = critic.check(record)
    assert not result.passed
    assert any("model_guidance_ref" in e for e in result.hard_errors)


def test_critic_nonexistent_model_guidance_ref_fails() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        model_guidance_ref="docs/model_guides/does_not_exist.yaml"
    )
    result = critic.check(record)
    assert not result.passed
    assert any("not found" in e for e in result.hard_errors)


def test_critic_model_id_mismatch_fails() -> None:
    """midjourney target_model but chatgpt_image guide → fails."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        target_models=["midjourney"],
        model_guidance_ref="docs/model_guides/chatgpt_image.yaml",
    )
    result = critic.check(record)
    assert not result.passed
    assert any("model_id" in e for e in result.hard_errors)


def test_critic_missing_negative_prompt_for_midjourney_fails() -> None:
    """Midjourney requires negative_prompt (limited support)."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(negative_prompt=None)
    result = critic.check(record)
    assert not result.passed
    assert any("negative_prompt" in e for e in result.hard_errors)


def test_critic_chatgpt_image_missing_constraint_strategy_fails() -> None:
    """ChatGPT Image without constraint_strategy fails."""
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        prompt_id="SC0003__t2i-char-c01-chatgpt-image__v01",
        target_models=["chatgpt_image"],
        model_guidance_ref="docs/model_guides/chatgpt_image.yaml",
        negative_prompt=None,
        # no constraint_strategy
    )
    result = critic.check(record)
    assert not result.passed
    assert any("constraint_strategy" in e for e in result.hard_errors)


def test_critic_dynamic_snapshot_missing_fails(tmp_path: Path) -> None:
    """Dynamic snapshot mode with non-existent snapshot file fails."""
    # Copy real repo guides into tmp_path so model_guidance_ref resolves
    import shutil
    (tmp_path / "docs" / "model_guides").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "docs" / "model_guides" / "midjourney.yaml",
                tmp_path / "docs" / "model_guides" / "midjourney.yaml")
    (tmp_path / "schemas").mkdir()
    shutil.copy(REPO_ROOT / "schemas" / "prompt_record.schema.json",
                tmp_path / "schemas" / "prompt_record.schema.json")

    critic = CriticAgent(tmp_path)
    record = _make_valid_record(
        model_guidance_mode="dynamic_snapshot",
        model_guidance_snapshot="evidence/model_guidance_snapshots/nonexistent.yaml",
    )
    result = critic.check(record)
    assert not result.passed
    assert any("snapshot" in e.lower() for e in result.hard_errors)


# ---------------------------------------------------------------------------
# CriticAgent — soft checks
# ---------------------------------------------------------------------------


def test_critic_unresolved_in_prompt_text_is_soft_warning() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record(
        prompt_text="Nadia Vale, UNRESOLVED state, lean silhouette"
    )
    result = critic.check(record)
    assert result.passed is False or (
        result.passed and any("UNRESOLVED" in w for w in result.soft_warnings)
    )
    # Specifically: soft warning must be present
    assert any("UNRESOLVED" in w for w in result.soft_warnings)


def test_critic_clean_record_has_no_soft_warnings() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = _make_valid_record()
    result = critic.check(record)
    assert result.soft_warnings == []


# ---------------------------------------------------------------------------
# PromptWriter — file I/O
# ---------------------------------------------------------------------------


def test_writer_creates_prompt_yaml(tmp_path: Path) -> None:
    writer = PromptWriter(tmp_path)
    record = _make_valid_record()
    run_record = _make_valid_run_record()

    result = writer.write(record, run_record)

    assert result.prompt_path.exists()
    assert result.prompt_path.name == "SC0003__t2i-char-c01-midjourney__v01.yaml"
    loaded = yaml.safe_load(result.prompt_path.read_text(encoding="utf-8"))
    assert loaded["prompt_id"] == "SC0003__t2i-char-c01-midjourney__v01"


def test_writer_creates_run_record_yaml(tmp_path: Path) -> None:
    writer = PromptWriter(tmp_path)
    record = _make_valid_record()
    run_record = _make_valid_run_record()

    result = writer.write(record, run_record)

    assert result.run_path.exists()
    assert result.run_path.name == "RUN_SC0003_MJ_0001.yaml"
    loaded = yaml.safe_load(result.run_path.read_text(encoding="utf-8"))
    assert loaded["run_id"] == "RUN_SC0003_MJ_0001"
    assert loaded["model"] == "midjourney"


def test_writer_prompt_yaml_in_draft_subdirectory(tmp_path: Path) -> None:
    writer = PromptWriter(tmp_path)
    result = writer.write(_make_valid_record(), _make_valid_run_record())
    assert "prompts" in str(result.prompt_path)
    assert "draft" in str(result.prompt_path)


def test_writer_run_record_in_evidence_prompt_runs(tmp_path: Path) -> None:
    writer = PromptWriter(tmp_path)
    result = writer.write(_make_valid_record(), _make_valid_run_record())
    assert "evidence" in str(result.run_path)
    assert "prompt_runs" in str(result.run_path)


def test_writer_appends_scene_prompt_map_row(tmp_path: Path) -> None:
    # Create CSV with header
    csv_path = tmp_path / "evidence" / "scene_prompt_map.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text(
        "scene_id,prompt_id,prompt_type,lifecycle_stage,target_model,"
        "asset_ref,article3_flag,notes\n",
        encoding="utf-8",
    )

    writer = PromptWriter(tmp_path)
    writer.write(_make_valid_record(), _make_valid_run_record())

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 1
    assert rows[0]["scene_id"] == "SC0003"
    assert rows[0]["prompt_id"] == "SC0003__t2i-char-c01-midjourney__v01"
    assert rows[0]["asset_ref"] == "pending_generation"


def test_writer_appends_run_costs_row(tmp_path: Path) -> None:
    csv_path = tmp_path / "evidence" / "run_costs.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text(
        "run_id,scene_id,model,prompt_type,outputs_expected,"
        "cost_value,cost_unit,status\n",
        encoding="utf-8",
    )

    writer = PromptWriter(tmp_path)
    writer.write(_make_valid_record(), _make_valid_run_record())

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN_SC0003_MJ_0001"
    assert rows[0]["model"] == "midjourney"
    assert rows[0]["cost_unit"] == "credits"


def test_writer_updates_prompt_library(tmp_path: Path) -> None:
    lib_path = tmp_path / "prompts" / "prompt_library.yaml"
    lib_path.parent.mkdir(parents=True)
    lib_path.write_text(
        "version: '0.1.0'\ndescription: test\nprompts: []\n",
        encoding="utf-8",
    )

    writer = PromptWriter(tmp_path)
    result = writer.write(_make_valid_record(), _make_valid_run_record())

    assert result.library_updated is True
    lib = yaml.safe_load(lib_path.read_text(encoding="utf-8"))
    assert len(lib["prompts"]) == 1
    assert lib["prompts"][0]["prompt_id"] == "SC0003__t2i-char-c01-midjourney__v01"


def test_writer_library_idempotent_second_write(tmp_path: Path) -> None:
    """Writing the same prompt_id twice does not duplicate the library entry."""
    writer = PromptWriter(tmp_path)
    writer.write(_make_valid_record(), _make_valid_run_record())
    result2 = writer.write(_make_valid_record(), _make_valid_run_record())

    assert result2.library_updated is False  # already present

    lib_path = tmp_path / "prompts" / "prompt_library.yaml"
    lib = yaml.safe_load(lib_path.read_text(encoding="utf-8"))
    assert len(lib["prompts"]) == 1


def test_writer_non_draft_raises() -> None:
    writer = PromptWriter(Path("."))
    record = _make_valid_record(lifecycle_stage="review")
    run_record = _make_valid_run_record()
    with pytest.raises(WriterLifecycleError):
        writer.write(record, run_record)


def test_writer_creates_csv_with_header_if_absent(tmp_path: Path) -> None:
    """Writer creates the CSV with header when the file doesn't exist yet."""
    writer = PromptWriter(tmp_path)
    writer.write(_make_valid_record(), _make_valid_run_record())

    csv_path = tmp_path / "evidence" / "scene_prompt_map.csv"
    assert csv_path.exists()
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("scene_id")  # header present


# ---------------------------------------------------------------------------
# Integration: Critic → Writer pipeline
# ---------------------------------------------------------------------------


def test_critic_then_writer_integration(tmp_path: Path) -> None:
    """
    Integration: only write when critic passes.

    Valid record → critic passes → writer writes files.
    Invalid record → critic fails → writer is not called.
    """
    import shutil

    # Set up a minimal repo in tmp_path so the Critic can resolve file paths
    (tmp_path / "docs" / "model_guides").mkdir(parents=True)
    for guide in ("midjourney.yaml", "chatgpt_image.yaml"):
        shutil.copy(
            REPO_ROOT / "docs" / "model_guides" / guide,
            tmp_path / "docs" / "model_guides" / guide,
        )
    (tmp_path / "schemas").mkdir()
    shutil.copy(
        REPO_ROOT / "schemas" / "prompt_record.schema.json",
        tmp_path / "schemas" / "prompt_record.schema.json",
    )

    critic = CriticAgent(tmp_path)
    writer = PromptWriter(tmp_path)

    # Valid Midjourney record
    valid_record = _make_valid_record()
    run_record = _make_valid_run_record()

    result = critic.check(valid_record)
    assert result.passed, f"Expected pass: {result.hard_errors}"

    write_result = writer.write(valid_record, run_record)
    assert write_result.prompt_path.exists()
    assert write_result.run_path.exists()

    # Invalid record (no negative_prompt for Midjourney)
    invalid_record = _make_valid_record(
        prompt_id="SC0003__t2i-char-c01-midjourney__v02",
        negative_prompt=None,
    )
    fail_result = critic.check(invalid_record)
    assert not fail_result.passed

    # Writer should NOT be called for invalid records
    invalid_path = tmp_path / "prompts" / "draft" / "SC0003__t2i-char-c01-midjourney__v02.yaml"
    assert not invalid_path.exists()


def test_adapters_produce_critic_passing_records(tmp_path: Path) -> None:
    """
    End-to-end: adapter-generated records pass the Critic when using real model guides.

    This test bridges Batch 4 (adapters) and Batch 5 (critic).
    """
    import shutil

    from scripts.agents.adapters.midjourney import MidjourneyAdapter
    from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter
    from scripts.agents.adapters.nano_banana import NanaBananaAdapter
    from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor

    # Set up schemas and guides in tmp_path
    (tmp_path / "docs" / "model_guides").mkdir(parents=True)
    (tmp_path / "schemas").mkdir()
    for guide in ("midjourney.yaml", "chatgpt_image.yaml", "nano_banana.yaml"):
        shutil.copy(
            REPO_ROOT / "docs" / "model_guides" / guide,
            tmp_path / "docs" / "model_guides" / guide,
        )
    shutil.copy(
        REPO_ROOT / "schemas" / "prompt_record.schema.json",
        tmp_path / "schemas" / "prompt_record.schema.json",
    )

    # Create a brief with clean prompt text (no canonical IDs)
    brief = NeutralBrief(
        scene_id="SC0003",
        element_type="character",
        element_id="C01",
        element_name="Nadia Vale",
        visual_anchors=[
            VisualAnchor(
                description="Lean, upright, economical silhouette",
                source_field="character.C01.visual_profile.silhouette",
            ),
            VisualAnchor(
                description="Muted neutrals and controlled domestic tones",
                source_field="character.C01.visual_profile.color_bias",
            ),
        ],
        negative_constraints=[
            "Neon cyberpunk color design",
            "Do not soften her into generalized maternal warmth",
        ],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
    )

    critic = CriticAgent(tmp_path)

    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(brief)
        result = critic.check(record)
        assert result.passed, (
            f"{AdapterCls.__name__} generated record failed critic:\n"
            + "\n".join(result.hard_errors)
        )
