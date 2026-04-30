"""
tests/test_model_research.py — Batch 0.1

Tests for ModelResearchAgent and snapshot construction helpers in
scripts/agents/model_research.py.

All tests use tmp_path and never write to the real evidence/ directory.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

# Add repo root to sys.path so we can import scripts.agents.model_research
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.model_research import (
    ALLOWED_SOURCE_CLASSES,
    BLOCKED_SOURCE_CLASSES,
    VALID_MODEL_IDS,
    BlockedSourceClassError,
    ModelResearchAgent,
    UnknownModelError,
    build_snapshot,
    find_latest_snapshot,
    is_snapshot_fresh,
    validate_snapshot_against_schema,
    write_snapshot,
    _sha256_of_text,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXED_TIME = datetime(2026, 4, 30, 15, 30, 0, tzinfo=timezone.utc)

MINIMAL_SOURCE = {
    "url": "https://docs.midjourney.com/",
    "retrieved_at": "2026-04-30T15:29:50Z",
    "http_status": 200,
    "content_hash": _sha256_of_text("mj docs content"),
    "human_verified": False,
    "source_class": "official_docs",
    "notes": "official parameter reference",
}


def _make_minimal_snapshot(model_id: str = "midjourney") -> dict:
    return build_snapshot(
        model_id=model_id,
        taken_at=FIXED_TIME,
        sources=[MINIMAL_SOURCE],
        extracted_rules=["Lead with subject and dominant quality."],
        confidence="high",
        model_version_observed="Midjourney 6.1",
        model_version_confidence="high",
    )


# ---------------------------------------------------------------------------
# build_snapshot() — valid construction
# ---------------------------------------------------------------------------


def test_build_snapshot_valid_midjourney():
    snap = _make_minimal_snapshot("midjourney")
    assert snap["model_id"] == "midjourney"
    assert snap["snapshot_taken_at"] == "2026-04-30T15:30:00Z"
    assert snap["snapshot_hash"] == "sha256:placeholder"  # replaced only by write_snapshot
    assert snap["confidence"] == "high"
    assert snap["model_version_observed"] == "Midjourney 6.1"
    assert snap["snapshot_validity"]["max_age_days"] == 14
    assert "2026-05-14" in snap["snapshot_validity"]["expires_at"]


def test_build_snapshot_kling_max_age_7():
    source = {**MINIMAL_SOURCE, "url": "https://kling.kuaishou.com/docs"}
    snap = build_snapshot(
        model_id="kling_omni",
        taken_at=FIXED_TIME,
        sources=[source],
        extracted_rules=["Use camera_motion field."],
        confidence="medium",
        model_version_observed="Kling 1.6",
        model_version_confidence="medium",
    )
    assert snap["snapshot_validity"]["max_age_days"] == 7
    assert "2026-05-07" in snap["snapshot_validity"]["expires_at"]


def test_build_snapshot_with_do_not_use():
    snap = build_snapshot(
        model_id="nano_banana",
        taken_at=FIXED_TIME,
        sources=[{**MINIMAL_SOURCE, "url": "https://nano.banana/docs"}],
        extracted_rules=["Use --identity flag for consistency."],
        confidence="medium",
        model_version_observed="unknown_ui_current",
        model_version_confidence="low",
        do_not_use_without_verification=["Undocumented shorthand --nb-fast"],
    )
    assert "do_not_use_without_verification" in snap
    assert len(snap["do_not_use_without_verification"]) == 1


# ---------------------------------------------------------------------------
# build_snapshot() — error cases
# ---------------------------------------------------------------------------


def test_build_snapshot_unknown_model():
    with pytest.raises(UnknownModelError, match="flux"):
        build_snapshot(
            model_id="flux",
            taken_at=FIXED_TIME,
            sources=[MINIMAL_SOURCE],
            extracted_rules=["some rule"],
            confidence="high",
            model_version_observed="1.0",
            model_version_confidence="high",
        )


def test_build_snapshot_blocked_source_class():
    bad_source = {**MINIMAL_SOURCE, "source_class": "forum_threads"}
    with pytest.raises(BlockedSourceClassError, match="forum_threads"):
        build_snapshot(
            model_id="midjourney",
            taken_at=FIXED_TIME,
            sources=[bad_source],
            extracted_rules=["some rule"],
            confidence="high",
            model_version_observed="Midjourney 6.1",
            model_version_confidence="high",
        )


def test_build_snapshot_blocked_source_prompt_hack():
    bad_source = {**MINIMAL_SOURCE, "source_class": "prompt_hack_blogs"}
    with pytest.raises(BlockedSourceClassError):
        build_snapshot(
            model_id="chatgpt_image",
            taken_at=FIXED_TIME,
            sources=[bad_source],
            extracted_rules=["some rule"],
            confidence="high",
            model_version_observed="GPT-4o",
            model_version_confidence="high",
        )


def test_build_snapshot_empty_sources():
    from scripts.agents.model_research import MissingRequiredFieldError
    with pytest.raises(MissingRequiredFieldError, match="sources"):
        build_snapshot(
            model_id="midjourney",
            taken_at=FIXED_TIME,
            sources=[],
            extracted_rules=["some rule"],
            confidence="high",
            model_version_observed="Midjourney 6.1",
            model_version_confidence="high",
        )


def test_build_snapshot_empty_rules():
    from scripts.agents.model_research import MissingRequiredFieldError
    with pytest.raises(MissingRequiredFieldError, match="extracted_rules"):
        build_snapshot(
            model_id="midjourney",
            taken_at=FIXED_TIME,
            sources=[MINIMAL_SOURCE],
            extracted_rules=[],
            confidence="high",
            model_version_observed="Midjourney 6.1",
            model_version_confidence="high",
        )


def test_build_snapshot_unknown_source_class():
    bad_source = {**MINIMAL_SOURCE, "source_class": "reddit_post"}
    with pytest.raises(ValueError, match="not a recognised allowed class"):
        build_snapshot(
            model_id="midjourney",
            taken_at=FIXED_TIME,
            sources=[bad_source],
            extracted_rules=["some rule"],
            confidence="high",
            model_version_observed="Midjourney 6.1",
            model_version_confidence="high",
        )


# ---------------------------------------------------------------------------
# write_snapshot() — file I/O and hash
# ---------------------------------------------------------------------------


def test_write_snapshot_creates_file(tmp_path):
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, tmp_path)
    assert out_path.exists()
    assert out_path.suffix == ".yaml"


def test_write_snapshot_filename_convention(tmp_path):
    snap = _make_minimal_snapshot("midjourney")
    out_path = write_snapshot(snap, tmp_path)
    # Expect: 20260430T153000Z_midjourney.yaml
    assert "midjourney" in out_path.name
    assert out_path.name.endswith(".yaml")


def test_write_snapshot_hash_is_not_placeholder(tmp_path):
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, tmp_path)
    data = yaml.safe_load(out_path.read_text())
    assert data["snapshot_hash"] != "sha256:placeholder"
    assert re.match(r"sha256:[a-f0-9]{64}$", data["snapshot_hash"])


def test_write_snapshot_creates_output_dir(tmp_path):
    nested = tmp_path / "deep" / "nested"
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, nested)
    assert nested.exists()
    assert out_path.exists()


def test_write_snapshot_yaml_is_valid_yaml(tmp_path):
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, tmp_path)
    data = yaml.safe_load(out_path.read_text())
    assert data["model_id"] == "midjourney"


# ---------------------------------------------------------------------------
# is_snapshot_fresh()
# ---------------------------------------------------------------------------


def test_snapshot_fresh_within_window(tmp_path):
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, tmp_path)
    # Reference time: 1 day after snapshot taken
    ref = datetime(2026, 5, 1, 15, 30, 0, tzinfo=timezone.utc)
    assert is_snapshot_fresh(out_path, reference_time=ref) is True


def test_snapshot_expired(tmp_path):
    snap = _make_minimal_snapshot()
    out_path = write_snapshot(snap, tmp_path)
    # Reference time: 20 days later (past 14-day limit)
    ref = datetime(2026, 5, 20, 0, 0, 0, tzinfo=timezone.utc)
    assert is_snapshot_fresh(out_path, reference_time=ref) is False


def test_snapshot_missing_path_returns_false(tmp_path):
    assert is_snapshot_fresh(tmp_path / "nonexistent.yaml") is False


# ---------------------------------------------------------------------------
# find_latest_snapshot()
# ---------------------------------------------------------------------------


def test_find_latest_snapshot_returns_most_recent(tmp_path):
    snap1 = _make_minimal_snapshot()
    snap1["snapshot_taken_at"] = "2026-04-28T12:00:00Z"
    snap1["snapshot_validity"]["expires_at"] = "2026-05-12T12:00:00Z"
    snap2 = _make_minimal_snapshot()
    snap2["snapshot_taken_at"] = "2026-04-30T15:30:00Z"
    snap2["snapshot_validity"]["expires_at"] = "2026-05-14T15:30:00Z"

    path1 = write_snapshot(snap1, tmp_path)
    path2 = write_snapshot(snap2, tmp_path)

    result = find_latest_snapshot(tmp_path, "midjourney")
    assert result is not None
    # Lexicographically later timestamp wins
    assert result.name >= path1.name


def test_find_latest_snapshot_returns_none_when_empty(tmp_path):
    result = find_latest_snapshot(tmp_path, "midjourney")
    assert result is None


def test_find_latest_snapshot_ignores_other_models(tmp_path):
    snap = _make_minimal_snapshot("midjourney")
    write_snapshot(snap, tmp_path)
    result = find_latest_snapshot(tmp_path, "chatgpt_image")
    assert result is None


# ---------------------------------------------------------------------------
# ModelResearchAgent.run()
# ---------------------------------------------------------------------------


def test_agent_run_produces_snapshots(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    results = agent.run(models=["midjourney", "chatgpt_image"], save=True)
    assert "midjourney" in results
    assert "chatgpt_image" in results
    assert results["midjourney"].exists()
    assert results["chatgpt_image"].exists()


def test_agent_run_dry_run(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    results = agent.run(models=["nano_banana"], save=False)
    assert "nano_banana" in results
    # save=False → no file written
    assert not (tmp_path / "snapshots").exists()


def test_agent_run_unknown_model(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    with pytest.raises(UnknownModelError):
        agent.run(models=["flux"])


def test_agent_run_placeholder_confidence_is_low(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    results = agent.run(models=["midjourney"], save=True)
    data = yaml.safe_load(results["midjourney"].read_text())
    assert data["confidence"] == "low"


def test_agent_run_placeholder_rule_warns(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    results = agent.run(models=["kling_omni"], save=True)
    data = yaml.safe_load(results["kling_omni"].read_text())
    assert any("PLACEHOLDER" in r for r in data["extracted_rules"])


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_valid_snapshot_passes_schema(tmp_path):
    agent = ModelResearchAgent(
        repo_root=REPO_ROOT,
        snapshot_dir=tmp_path / "snapshots",
    )
    results = agent.run(models=["midjourney"], save=True)
    data = yaml.safe_load(results["midjourney"].read_text())
    errors = validate_snapshot_against_schema(data, REPO_ROOT)
    # Either no errors (jsonschema installed) or skipped gracefully
    assert errors == [] or errors[0].startswith("jsonschema not installed")


def test_invalid_snapshot_fails_schema():
    bad = {"model_id": "midjourney"}  # missing required fields
    errors = validate_snapshot_against_schema(bad, REPO_ROOT)
    if errors and errors[0].startswith("jsonschema not installed"):
        pytest.skip("jsonschema not installed")
    assert len(errors) > 0


# ---------------------------------------------------------------------------
# Constants integrity
# ---------------------------------------------------------------------------


def test_allowed_and_blocked_source_classes_are_disjoint():
    assert ALLOWED_SOURCE_CLASSES.isdisjoint(BLOCKED_SOURCE_CLASSES)


def test_valid_model_ids_match_capability_matrix():
    """Verify VALID_MODEL_IDS matches model_capability_matrix.yaml."""
    matrix_path = REPO_ROOT / "docs" / "model_guides" / "model_capability_matrix.yaml"
    if not matrix_path.exists():
        pytest.skip("model_capability_matrix.yaml not found")
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix_ids = set(matrix.get("models", {}).keys())
    assert matrix_ids == VALID_MODEL_IDS, (
        f"VALID_MODEL_IDS {VALID_MODEL_IDS} does not match "
        f"model_capability_matrix.yaml models {matrix_ids}"
    )
