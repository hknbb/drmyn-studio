"""
Planning Name Leakage Guard tests.

Verifies that T2I adapter outputs never contain planning display names,
character surnames, or location canonical names in prompt_text, and that
the Critic blocks such leakage when planning_name_filter metadata is present.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agents.critic import CriticAgent
from scripts.agents.neutral_brief import (
    NeutralBrief,
    VisualAnchor,
    _planning_aliases_for,
    _safe_subject_label,
)
from scripts.agents.adapters.midjourney import MidjourneyAdapter
from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter
from scripts.agents.adapters.nano_banana import NanaBananaAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]

_VA = lambda desc: VisualAnchor(description=desc, source_field="x")


def _char_brief(element_name: str = "Nadia Vale") -> NeutralBrief:
    return NeutralBrief(
        scene_id="SC0003",
        element_type="character",
        element_id="C01",
        element_name=element_name,
        visual_anchors=[_VA("Lean, upright, economical silhouette.")],
        negative_constraints=["Neon cyberpunk color design."],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        prompt_subject_label=_safe_subject_label(element_name, "character"),
        planning_aliases=_planning_aliases_for(element_name, "character"),
    )


def _loc_brief(element_name: str = "Vale Residence, Vardova") -> NeutralBrief:
    return NeutralBrief(
        scene_id="SC0001",
        element_type="location",
        element_id="LOC001",
        element_name=element_name,
        visual_anchors=[_VA("Pale stone, muted domestic neutrals.")],
        negative_constraints=[],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        prompt_subject_label=_safe_subject_label(element_name, "location"),
        planning_aliases=_planning_aliases_for(element_name, "location"),
    )


# ---------------------------------------------------------------------------
# Helper label extraction
# ---------------------------------------------------------------------------

def test_safe_subject_label_character_first_name_only() -> None:
    assert _safe_subject_label("Nadia Vale", "character") == "Nadia"


def test_safe_subject_label_single_name_character() -> None:
    assert _safe_subject_label("Birta", "character") == "Birta"


def test_safe_subject_label_location_is_empty() -> None:
    assert _safe_subject_label("Vale Residence, Vardova", "location") == ""


def test_planning_aliases_character_includes_full_name_only() -> None:
    # Surname is NOT a separate alias — it may appear in source-derived anchor text
    # (e.g. costume_logic referencing "Vale residence scenes")
    aliases = _planning_aliases_for("Nadia Vale", "character")
    assert "Nadia Vale" in aliases
    assert "Vale" not in aliases


def test_planning_aliases_location_includes_canonical_and_parts() -> None:
    aliases = _planning_aliases_for("Vale Residence, Vardova", "location")
    assert "Vale Residence, Vardova" in aliases
    assert "Vale Residence" in aliases
    assert "Vardova" in aliases


def test_planning_aliases_single_name_character_no_surname() -> None:
    aliases = _planning_aliases_for("Birta", "character")
    assert "Birta" in aliases
    assert len(aliases) == 1  # no separate surname token


# ---------------------------------------------------------------------------
# Adapter outputs — no planning names in prompt_text
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("AdapterCls", [MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter])
def test_adapter_does_not_leak_full_character_name(tmp_path: Path, AdapterCls) -> None:
    adapter = AdapterCls(tmp_path)
    brief = _char_brief("Nadia Vale")
    record, _ = adapter.generate(brief)
    assert "Nadia Vale" not in record["prompt_text"], (
        f"{AdapterCls.__name__} leaked 'Nadia Vale' into prompt_text"
    )


@pytest.mark.parametrize("AdapterCls", [MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter])
def test_adapter_uses_first_name_only(tmp_path: Path, AdapterCls) -> None:
    adapter = AdapterCls(tmp_path)
    brief = _char_brief("Nadia Vale")
    record, _ = adapter.generate(brief)
    assert "Nadia" in record["prompt_text"], (
        f"{AdapterCls.__name__} missing first-name 'Nadia' in prompt_text"
    )


@pytest.mark.parametrize("AdapterCls", [MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter])
def test_adapter_does_not_leak_location_canonical_name(tmp_path: Path, AdapterCls) -> None:
    adapter = AdapterCls(tmp_path)
    brief = _loc_brief("Vale Residence, Vardova")
    record, _ = adapter.generate(brief)
    assert "Vale Residence" not in record["prompt_text"], (
        f"{AdapterCls.__name__} leaked location canonical name into prompt_text"
    )
    assert "Vardova" not in record["prompt_text"]


# ---------------------------------------------------------------------------
# generation_params carries planning_name_filter
# ---------------------------------------------------------------------------

def test_generation_params_has_planning_name_filter(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    brief = _char_brief("Nadia Vale")
    record, _ = adapter.generate(brief)
    pnf = record["generation_params"].get("planning_name_filter", {})
    assert "Nadia Vale" in pnf.get("forbidden", [])
    # Surname "Vale" is NOT a separate alias — only full display name is forbidden
    assert "Vale" not in pnf.get("forbidden", [])


def test_no_planning_name_filter_when_no_aliases(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    brief = NeutralBrief(
        scene_id="SC0003", element_type="style", element_id="style_bible",
        element_name="Style Bible",
        visual_anchors=[_VA("Controlled world revealing machinery.")],
        negative_constraints=[], continuity_state=None,
        continuity_note=None, continuity_warning=None,
        model_guidance_required=True, is_ready=True,
    )
    record, _ = adapter.generate(brief)
    assert "planning_name_filter" not in record["generation_params"]


# ---------------------------------------------------------------------------
# Critic blocks planning aliases in prompt_text
# ---------------------------------------------------------------------------

def test_critic_blocks_full_name_in_prompt_text() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = {
        "prompt_id": "SC0003__t2i-char-c01-midjourney__v01",
        "scene_id": "SC0003",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0003/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0003/scene_excerpt.md",
        },
        "prompt_text": "Nadia Vale, lean upright silhouette",
        "negative_prompt": "neon cyberpunk",
        "generation_params": {
            "model_guidance_mode": "locked_guide",
            "model_guidance_ref": "docs/model_guides/midjourney.yaml",
            "adapter_name": "midjourney",
            "planning_name_filter": {"forbidden": ["Nadia Vale", "Vale"]},
        },
        "status": "active",
        "canon_lock": False,
    }
    result = critic.check(record)
    assert not result.passed
    assert any("Nadia Vale" in e for e in result.hard_errors)


def test_critic_blocks_any_alias_explicitly_declared_in_filter() -> None:
    # Critic blocks whatever is in planning_name_filter.forbidden, even single words.
    # (Real character aliases don't include surname, but location names might.)
    critic = CriticAgent(REPO_ROOT)
    record = {
        "prompt_id": "SC0001__t2i-loc-loc001-midjourney__v01",
        "scene_id": "SC0001",
        "prompt_type": "t2i_location_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
        },
        "prompt_text": "Vale Residence interior, pale stone, muted domestic neutrals",
        "generation_params": {
            "model_guidance_mode": "locked_guide",
            "model_guidance_ref": "docs/model_guides/midjourney.yaml",
            "adapter_name": "midjourney",
            "planning_name_filter": {"forbidden": ["Vale Residence, Vardova", "Vale Residence", "Vardova"]},
        },
        "status": "active",
        "canon_lock": False,
    }
    result = critic.check(record)
    assert not result.passed
    assert any("Vale Residence" in e for e in result.hard_errors)


def test_critic_passes_first_name_only() -> None:
    critic = CriticAgent(REPO_ROOT)
    record = {
        "prompt_id": "SC0003__t2i-char-c01-midjourney__v01",
        "scene_id": "SC0003",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0003/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0003/scene_excerpt.md",
        },
        "prompt_text": "Nadia, lean upright silhouette, muted domestic neutrals",
        "negative_prompt": "neon cyberpunk",
        "generation_params": {
            "model_guidance_mode": "locked_guide",
            "model_guidance_ref": "docs/model_guides/midjourney.yaml",
            "adapter_name": "midjourney",
            "planning_name_filter": {"forbidden": ["Nadia Vale", "Vale"]},
        },
        "status": "active",
        "canon_lock": False,
    }
    result = critic.check(record)
    # No planning alias errors
    alias_errors = [e for e in result.hard_errors if "Planning name" in e]
    assert alias_errors == []


def test_critic_no_planning_filter_metadata_no_alias_check() -> None:
    """Old records without planning_name_filter are not retroactively blocked."""
    critic = CriticAgent(REPO_ROOT)
    record = {
        "prompt_id": "SC0003__t2i-char-c01-midjourney__v01",
        "scene_id": "SC0003",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0003/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0003/scene_excerpt.md",
        },
        "prompt_text": "Nadia Vale, lean upright silhouette",
        "negative_prompt": "neon cyberpunk",
        "generation_params": {
            "model_guidance_mode": "locked_guide",
            "model_guidance_ref": "docs/model_guides/midjourney.yaml",
            "adapter_name": "midjourney",
            # No planning_name_filter — old record
        },
        "status": "active",
        "canon_lock": False,
    }
    result = critic.check(record)
    alias_errors = [e for e in result.hard_errors if "Planning name" in e]
    assert alias_errors == []
