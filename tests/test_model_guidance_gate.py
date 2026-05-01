from __future__ import annotations

import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.critic import CriticAgent  # noqa: E402
from scripts.agents.model_research import (  # noqa: E402
    ModelResearchAgent,
    build_snapshot,
    write_snapshot,
)
from scripts.agents.operator_next_step import recommend_next_step  # noqa: E402


REFERENCE_TIME = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _copy_critic_minimum(repo_root: Path) -> None:
    (repo_root / "schemas").mkdir(parents=True)
    shutil.copy(
        REPO_ROOT / "schemas" / "prompt_record.schema.json",
        repo_root / "schemas" / "prompt_record.schema.json",
    )
    (repo_root / "docs" / "model_guides").mkdir(parents=True)
    for name in ("midjourney.yaml", "chatgpt_image.yaml"):
        shutil.copy(
            REPO_ROOT / "docs" / "model_guides" / name,
            repo_root / "docs" / "model_guides" / name,
        )


def _prompt_record(
    *,
    model: str = "midjourney",
    guidance_ref: str = "docs/model_guides/midjourney.yaml",
    mode: str = "dynamic_snapshot",
    snapshot: str | None = None,
) -> dict:
    params = {
        "model_guidance_mode": mode,
        "model_guidance_ref": guidance_ref,
        "adapter_name": model,
    }
    if snapshot:
        params["model_guidance_snapshot"] = snapshot
    record = {
        "prompt_id": f"SC0001__t2i-char-c01-{model.replace('_', '-')}__v01",
        "scene_id": "SC0001",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": [model],
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
            "character_refs": ["C01"],
        },
        "prompt_text": "Nadia Vale, lean upright silhouette, muted domestic neutrals",
        "generation_params": params,
        "expected_output": {"asset_type": "image_set", "variation_count": 4},
        "status": "active",
        "canon_lock": False,
    }
    if model == "midjourney":
        record["negative_prompt"] = "neon cyberpunk, teal-orange grading"
    else:
        params["constraint_strategy"] = "embedded_positive_constraints"
    return record


def _valid_snapshot(repo_root: Path, *, model_id: str = "midjourney") -> Path:
    snapshot = build_snapshot(
        model_id=model_id,
        taken_at=REFERENCE_TIME,
        sources=[
            {
                "url": f"https://docs.example.com/{model_id}/official",
                "retrieved_at": "2026-05-01T12:00:00Z",
                "http_status": 200,
                "content_hash": _sha256_text(f"{model_id}:official-doc"),
                "human_verified": True,
                "source_class": "official_docs",
                "notes": "Human verified official documentation snapshot.",
            }
        ],
        extracted_rules=["Use concise subject-first visual clauses grounded in source records."],
        confidence="high",
        model_version_observed=f"{model_id}_current",
        model_version_confidence="high",
        do_not_use_without_verification=[],
    )
    return write_snapshot(snapshot, repo_root / "evidence" / "model_guidance_snapshots")


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def test_placeholder_snapshot_referenced_by_prompt_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = ModelResearchAgent(
        tmp_path,
        snapshot_dir=tmp_path / "evidence" / "model_guidance_snapshots",
    ).run(["midjourney"], save=True, reference_time=REFERENCE_TIME)["midjourney"]

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("placeholder" in error.lower() for error in result.hard_errors)


def test_valid_dynamic_snapshot_passes(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert result.passed, result.hard_errors


def test_expired_snapshot_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    data["snapshot_validity"]["expires_at"] = "2026-04-30T00:00:00Z"
    _write_yaml(snapshot, data)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("expired" in error.lower() for error in result.hard_errors)


def test_locked_guide_mode_still_passes_without_snapshot(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    record = _prompt_record(mode="locked_guide", snapshot=None)

    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert result.passed, result.hard_errors


def test_snapshot_model_id_mismatch_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path, model_id="chatgpt_image")

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("model_id" in error for error in result.hard_errors)


def test_placeholder_url_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    data["sources"][0]["url"] = "https://example.org/placeholder/midjourney"
    _write_yaml(snapshot, data)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("sources.0.url" in error for error in result.hard_errors)


def test_placeholder_rule_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    data["extracted_rules"] = ["PLACEHOLDER - replace before use."]
    _write_yaml(snapshot, data)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("PLACEHOLDER" in error for error in result.hard_errors)


def test_non_empty_do_not_use_without_verification_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    data["do_not_use_without_verification"] = ["Needs human verification."]
    _write_yaml(snapshot, data)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("do_not_use_without_verification" in error for error in result.hard_errors)


def test_unverified_snapshot_source_fails(tmp_path: Path) -> None:
    _copy_critic_minimum(tmp_path)
    snapshot = _valid_snapshot(tmp_path)
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    data["sources"][0]["human_verified"] = False
    _write_yaml(snapshot, data)

    record = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    result = CriticAgent(tmp_path, reference_time=REFERENCE_TIME).check(record)

    assert not result.passed
    assert any("human_verified" in error for error in result.hard_errors)


def test_operator_next_step_recommends_snapshot_refresh_for_placeholder(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path / "planning" / "scenes" / "SC0001" / "scene_card.yaml",
        {"scene_id": "SC0001", "excerpt_ref": "scene_excerpt.md"},
    )
    (tmp_path / "planning" / "scenes" / "SC0001" / "scene_excerpt.md").write_text(
        "Scene excerpt.",
        encoding="utf-8",
    )
    snapshot = ModelResearchAgent(
        tmp_path,
        snapshot_dir=tmp_path / "evidence" / "model_guidance_snapshots",
    ).run(["midjourney"], save=True, reference_time=REFERENCE_TIME)["midjourney"]
    prompt = _prompt_record(snapshot=_rel(snapshot, tmp_path))
    _write_yaml(tmp_path / "prompts" / "draft" / "prompt.yaml", prompt)

    step = recommend_next_step(tmp_path)

    assert step.current_task == "model_guidance_snapshot_refresh"
    assert step.allowed_commands == ("switch", "revise")
    assert _rel(snapshot, tmp_path) in step.open_files
