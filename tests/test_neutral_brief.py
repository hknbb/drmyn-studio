"""
tests/test_neutral_brief.py — Batch 3

Tests for the Neutral Brief Agent and related helpers.
- Unit tests for each element-type builder
- Style-bible extraction
- Continuity state flow (prop + wardrobe)
- Readiness flags (UNRESOLVED → is_ready=False)
- Integration test against real SC0003 data

All resolver tests use tmp_path — real planning/ files are only touched by
the integration tests that explicitly read SC0003.
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.neutral_brief import (  # noqa: E402
    NeutralBrief,
    NeutralBriefAgent,
    VisualAnchor,
    _extract_style_do_not_rules,
)
from scripts.agents.source_context import SourceContext, SourceContextAgent  # noqa: E402


# ---------------------------------------------------------------------------
# Inline fixtures
# ---------------------------------------------------------------------------

CHAR_C01 = {
    "character_id": "C01",
    "display_name": "Nadia Vale",
    "visual_profile": {
        "age_range": "early to mid 30s",
        "screen_presence": "Controlled, observant, and physically exact.",
        "silhouette": "Lean, upright, economical silhouette.",
        "color_bias": "Muted neutrals and controlled domestic tones.",
        "costume_logic": "Elite domestic presentation, always practical.",
        "hair_makeup_notes": "Natural restraint over glamor.",
    },
    "do_not_invent_notes": [
        "Do not soften her into generalized maternal warmth.",
        "Do not style her as action-invulnerable or fashion-forward.",
    ],
}

LOC001 = {
    "location_id": "LOC001",
    "canonical_name": "Vale Residence, Vardova",
    "visual_profile": {
        "palette": "Pale stone, muted creams, cold domestic neutrals.",
        "architecture_logic": "Winged elite residence built around curation.",
        "lighting_logic": "Filtered daylight and controlled practical pools.",
        "camera_behavior": "Thresholds, corridor depth, and slight object deviations.",
        "sound_texture": "Quiet house ambience and nursery white noise.",
        "spatial_motifs": ["thresholds", "surveillance geometry"],
    },
    "material_profile": ["pale stone", "muted domestic luxury surfaces"],
    "texture_profile": ["expensive underuse", "dust-shadow evidence"],
    "stable_visual_rules": ["Wealth should read as curation and underuse, not warmth."],
    "emotional_register": "Contained dread, performed order.",
    "non_invention_rules": [
        "Do not turn the residence into gothic excess.",
        "Do not over-decorate Jin's spaces beyond source-supported care detail.",
    ],
}

PROP001 = {
    "prop_id": "PROP001",
    "canonical_name": "Jin's medical bracelet",
    "visual_description": "Thin hospital-style plastic bracelet with printed ID strip.",
    "physical_description_grounded": "SC0003: white plastic with a small printed ID strip.",
    "visual_stability_notes": [
        "SC0003 bracelet is white plastic. SC0010-SC0014 bracelet is pale blue.",
    ],
    "handling_notes": [
        "Keep it ordinary and medically plausible, not tech-futuristic.",
    ],
    "status": "review",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "White plastic hospital bracelet; Nadia listed as registrant.",
        "state_changes": [
            {
                "scene_id": "SC0010",
                "transition_note": "Replacement bracelet applied at a more recent visit.",
                "new_state": "Pale blue band from a later check-up.",
            }
        ],
    },
}

WD001 = {
    "wardrobe_id": "WD001",
    "name": "Nadia domestic control look",
    "visual_description": "Controlled early-day domestic clothing with clean lines.",
    "color_profile": "Muted domestic neutrals.",
    "silhouette": "Lean, upright, contained.",
    "material_notes": "Practical, polished, and quiet rather than luxurious.",
    "palette_bias": "Muting over saturation.",
    "semiotic_function": "Signals composed domestic performance under pressure.",
    "continuity_constraints": [
        "Must remain consistent between SC0001 and SC0003.",
        "Should support floor sitting and corridor movement without feeling styled for display.",
    ],
    "status": "review",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "Early domestic continuity state for the Vale residence morning cluster.",
        "state_changes": [],
    },
}

PROP_UNRESOLVED = {
    "prop_id": "PROP999",
    "canonical_name": "Unresolved test prop",
    "visual_description": "Test prop.",
    "status": "draft",
    "canon_lock": False,
    "continuity_state": {
        "initial_state": "UNRESOLVED: exact state unknown at this time.",
        "state_changes": [],
    },
}

STYLE_TEXT = dedent(
    """\
    ## Visual thesis

    This project should look like a controlled world revealing its machinery.

    ## Palette rules

    Confirmed palette evidence:
    - Pale stone, muted cream, and cold domestic neutrals in the Vale residence.

    Do not do:
    - Neon cyberpunk color design.
    - Teal-orange blockbuster simplification.
    - Golden sentimental domestic warmth as a default treatment.

    ## Negative visual rules

    - No glossy near-future luxury fetish.
    - No comic-book violence.

    ## Do-not-drift list

    - Do not drift from grounded near-future into overt science fiction.
    - Do not drift from physical cost into action invulnerability.
    """
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _make_repo(
    tmp_path: Path,
    *,
    props: dict | None = None,
    wardrobe: dict | None = None,
) -> Path:
    """Write prop and wardrobe YAML files into a minimal repo structure."""
    for prop_id, data in (props or {}).items():
        _write_yaml(tmp_path / "planning" / "props" / f"{prop_id}.yaml", data)
    for ward_id, data in (wardrobe or {}).items():
        _write_yaml(tmp_path / "planning" / "wardrobe" / f"{ward_id}.yaml", data)
    return tmp_path


def _context(
    *,
    scene_id: str = "SC0001",
    characters: dict | None = None,
    location: dict | None = None,
    props: dict | None = None,
    wardrobe: dict | None = None,
    style_bible_text: str | None = None,
) -> SourceContext:
    return SourceContext(
        scene_id=scene_id,
        scene_card={},
        scene_excerpt=None,
        characters=characters or {},
        location=location,
        props=props or {},
        wardrobe=wardrobe or {},
        style_bible_text=style_bible_text,
        unresolved_warnings=[],
        missing_records=[],
        escalate=False,
    )


# ---------------------------------------------------------------------------
# Style rule extraction tests
# ---------------------------------------------------------------------------


def test_extract_do_not_section_bullets() -> None:
    """Formal 'Do not do:' section bullets are captured."""
    rules = _extract_style_do_not_rules(STYLE_TEXT)
    assert "Neon cyberpunk color design." in rules
    assert "Teal-orange blockbuster simplification." in rules
    assert "Golden sentimental domestic warmth as a default treatment." in rules


def test_extract_no_bullets_outside_section() -> None:
    """'- No ...' bullets are captured outside formal sections."""
    rules = _extract_style_do_not_rules(STYLE_TEXT)
    assert "No glossy near-future luxury fetish." in rules
    assert "No comic-book violence." in rules


def test_extract_do_not_drift_bullets() -> None:
    """'- Do not ...' bullets under a non-standard section header are captured."""
    rules = _extract_style_do_not_rules(STYLE_TEXT)
    assert "Do not drift from grounded near-future into overt science fiction." in rules
    assert "Do not drift from physical cost into action invulnerability." in rules


def test_extract_no_duplication() -> None:
    """Each distinct rule appears exactly once in the output."""
    rules = _extract_style_do_not_rules(STYLE_TEXT)
    assert len(rules) == len(set(rules))


def test_extract_empty_style_text() -> None:
    """Empty or None style text returns an empty list without error."""
    assert _extract_style_do_not_rules("") == []


def test_real_style_bible_extracts_expected_rule_count() -> None:
    """Real style_bible.md produces at least 10 negative constraints."""
    style_path = REPO_ROOT / "source" / "style_bible.md"
    if not style_path.exists():
        pytest.skip("style_bible.md not found")
    rules = _extract_style_do_not_rules(style_path.read_text(encoding="utf-8"))
    assert len(rules) >= 10, f"Expected >= 10 rules, got {len(rules)}: {rules}"


# ---------------------------------------------------------------------------
# Character brief tests
# ---------------------------------------------------------------------------


def test_character_brief_has_visual_anchors(tmp_path: Path) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(characters={"C01": CHAR_C01})
    briefs = agent.build_scene_briefs(ctx)

    char_brief = next(b for b in briefs if b.element_type == "character")
    anchor_texts = [a.description for a in char_brief.visual_anchors]

    assert any("muted" in t.lower() for t in anchor_texts), "color_bias missing"
    assert any("lean" in t.lower() for t in anchor_texts), "silhouette missing"
    assert char_brief.element_id == "C01"
    assert char_brief.element_name == "Nadia Vale"


def test_character_brief_source_fields_are_cited(tmp_path: Path) -> None:
    """Every visual anchor has a non-empty source_field."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(characters={"C01": CHAR_C01})
    briefs = agent.build_scene_briefs(ctx)
    char_brief = next(b for b in briefs if b.element_type == "character")

    for anchor in char_brief.visual_anchors:
        assert anchor.source_field, f"Empty source_field: {anchor}"
        assert anchor.source_field.startswith("character.C01")


def test_character_brief_do_not_invent_notes_in_constraints(
    tmp_path: Path,
) -> None:
    """do_not_invent_notes flow into negative_constraints."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(characters={"C01": CHAR_C01})
    briefs = agent.build_scene_briefs(ctx)
    char_brief = next(b for b in briefs if b.element_type == "character")

    joined = "\n".join(char_brief.negative_constraints).lower()
    assert "maternal warmth" in joined
    assert "action-invulnerable" in joined


def test_character_brief_style_rules_in_constraints(tmp_path: Path) -> None:
    """Style bible 'Do not do:' rules appear in character brief constraints."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(characters={"C01": CHAR_C01}, style_bible_text=STYLE_TEXT)
    briefs = agent.build_scene_briefs(ctx)
    char_brief = next(b for b in briefs if b.element_type == "character")

    joined = "\n".join(char_brief.negative_constraints).lower()
    assert "neon cyberpunk" in joined


def test_character_brief_no_continuity_state(tmp_path: Path) -> None:
    """Character briefs have no continuity_state (handled by wardrobe/prop)."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(characters={"C01": CHAR_C01})
    briefs = agent.build_scene_briefs(ctx)
    char_brief = next(b for b in briefs if b.element_type == "character")

    assert char_brief.continuity_state is None
    assert char_brief.continuity_warning is None


# ---------------------------------------------------------------------------
# Location brief tests
# ---------------------------------------------------------------------------


def test_location_brief_has_visual_anchors(tmp_path: Path) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(location=LOC001)
    briefs = agent.build_scene_briefs(ctx)

    loc_brief = next(b for b in briefs if b.element_type == "location")
    anchor_texts = [a.description for a in loc_brief.visual_anchors]

    assert any("pale stone" in t.lower() for t in anchor_texts), "palette missing"
    assert any("threshold" in t.lower() for t in anchor_texts), "spatial_motifs missing"


def test_location_brief_non_invention_rules_in_constraints(
    tmp_path: Path,
) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(location=LOC001)
    briefs = agent.build_scene_briefs(ctx)

    loc_brief = next(b for b in briefs if b.element_type == "location")
    joined = "\n".join(loc_brief.negative_constraints).lower()
    assert "gothic excess" in joined
    assert "over-decorate" in joined


def test_location_brief_element_id_and_name(tmp_path: Path) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(location=LOC001)
    briefs = agent.build_scene_briefs(ctx)
    loc_brief = next(b for b in briefs if b.element_type == "location")

    assert loc_brief.element_id == "LOC001"
    assert "Vale Residence" in loc_brief.element_name


# ---------------------------------------------------------------------------
# Prop brief tests
# ---------------------------------------------------------------------------


def test_prop_brief_continuity_state_initial_before_sc0010(
    tmp_path: Path,
) -> None:
    """PROP001 at SC0003 (before change) → white plastic state."""
    repo = _make_repo(tmp_path, props={"PROP001": PROP001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0003", props={"PROP001": PROP001})
    briefs = agent.build_scene_briefs(ctx)
    prop_brief = next(b for b in briefs if b.element_type == "prop")

    assert prop_brief.continuity_state is not None
    assert "white plastic" in prop_brief.continuity_state.lower()
    assert prop_brief.is_ready is True
    assert prop_brief.continuity_warning is None


def test_prop_brief_continuity_state_updated_at_sc0010(tmp_path: Path) -> None:
    """PROP001 at SC0010 (at change) → pale blue state."""
    repo = _make_repo(tmp_path, props={"PROP001": PROP001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0010", props={"PROP001": PROP001})
    briefs = agent.build_scene_briefs(ctx)
    prop_brief = next(b for b in briefs if b.element_type == "prop")

    assert "pale blue" in prop_brief.continuity_state.lower()
    assert prop_brief.is_ready is True


def test_prop_brief_unresolved_continuity_sets_is_ready_false(
    tmp_path: Path,
) -> None:
    """UNRESOLVED continuity state → is_ready=False and continuity_warning set."""
    repo = _make_repo(tmp_path, props={"PROP999": PROP_UNRESOLVED})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0001", props={"PROP999": PROP_UNRESOLVED})
    briefs = agent.build_scene_briefs(ctx)
    prop_brief = next(b for b in briefs if b.element_type == "prop")

    assert prop_brief.is_ready is False
    assert prop_brief.continuity_warning is not None
    assert "unresolved" in prop_brief.continuity_warning.lower()
    assert "UNRESOLVED" in prop_brief.continuity_state


def test_prop_brief_missing_record_does_not_crash(tmp_path: Path) -> None:
    """Missing prop file in repo → brief generated with continuity_state=None."""
    # No prop files written to tmp_path; resolver will silently fail
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(
        scene_id="SC0001",
        props={
            "PROP404": {
                "prop_id": "PROP404",
                "name": "Ghost prop",
                "visual_description": "A prop with no backing file.",
                "status": "draft",
                "canon_lock": False,
            }
        },
    )
    briefs = agent.build_scene_briefs(ctx)
    prop_brief = next(b for b in briefs if b.element_type == "prop")

    assert prop_brief.continuity_state is None
    assert prop_brief.continuity_warning is None


def test_prop_brief_handling_notes_in_constraints(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, props={"PROP001": PROP001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0001", props={"PROP001": PROP001})
    briefs = agent.build_scene_briefs(ctx)
    prop_brief = next(b for b in briefs if b.element_type == "prop")

    joined = "\n".join(prop_brief.negative_constraints).lower()
    assert "medically plausible" in joined


# ---------------------------------------------------------------------------
# Wardrobe brief tests
# ---------------------------------------------------------------------------


def test_wardrobe_brief_continuity_state_initial(tmp_path: Path) -> None:
    """WD001 at any scene → initial state (no state_changes)."""
    repo = _make_repo(tmp_path, wardrobe={"WD001": WD001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0003", wardrobe={"WD001": WD001})
    briefs = agent.build_scene_briefs(ctx)
    ward_brief = next(b for b in briefs if b.element_type == "wardrobe")

    assert ward_brief.continuity_state is not None
    assert "early domestic" in ward_brief.continuity_state.lower()
    assert ward_brief.is_ready is True
    assert ward_brief.continuity_warning is None


def test_wardrobe_brief_continuity_constraints_in_negative(tmp_path: Path) -> None:
    """WD001 continuity_constraints flow into negative_constraints."""
    repo = _make_repo(tmp_path, wardrobe={"WD001": WD001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0001", wardrobe={"WD001": WD001})
    briefs = agent.build_scene_briefs(ctx)
    ward_brief = next(b for b in briefs if b.element_type == "wardrobe")

    joined = "\n".join(ward_brief.negative_constraints).lower()
    assert "consistent" in joined


def test_wardrobe_brief_has_visual_anchors(tmp_path: Path) -> None:
    """Wardrobe brief includes visual fields as anchors."""
    repo = _make_repo(tmp_path, wardrobe={"WD001": WD001})
    agent = NeutralBriefAgent(repo)
    ctx = _context(scene_id="SC0001", wardrobe={"WD001": WD001})
    briefs = agent.build_scene_briefs(ctx)
    ward_brief = next(b for b in briefs if b.element_type == "wardrobe")

    anchor_texts = [a.description for a in ward_brief.visual_anchors]
    assert any("muted domestic" in t.lower() for t in anchor_texts)


def test_wardrobe_brief_missing_record_does_not_crash(tmp_path: Path) -> None:
    """Missing wardrobe file → brief with continuity_state=None, no exception."""
    agent = NeutralBriefAgent(tmp_path)  # empty repo
    ctx = _context(
        scene_id="SC0001",
        wardrobe={
            "WD999": {
                "wardrobe_id": "WD999",
                "name": "Ghost wardrobe",
                "visual_description": "Does not exist on disk.",
                "status": "draft",
                "canon_lock": False,
            }
        },
    )
    briefs = agent.build_scene_briefs(ctx)
    ward_brief = next(b for b in briefs if b.element_type == "wardrobe")

    assert ward_brief.continuity_state is None


# ---------------------------------------------------------------------------
# Style brief tests
# ---------------------------------------------------------------------------


def test_style_brief_has_do_not_rules(tmp_path: Path) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(style_bible_text=STYLE_TEXT)
    briefs = agent.build_scene_briefs(ctx)
    style_brief = next(b for b in briefs if b.element_type == "style")

    joined = "\n".join(style_brief.negative_constraints).lower()
    assert "neon cyberpunk" in joined
    assert "teal-orange" in joined
    assert "no glossy" in joined
    assert "do not drift" in joined


def test_style_brief_element_id_and_type(tmp_path: Path) -> None:
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(style_bible_text=STYLE_TEXT)
    briefs = agent.build_scene_briefs(ctx)
    style_brief = next(b for b in briefs if b.element_type == "style")

    assert style_brief.element_id == "style_bible"
    assert style_brief.element_type == "style"
    assert style_brief.model_guidance_required is True


def test_style_brief_has_visual_thesis_anchor(tmp_path: Path) -> None:
    """Style brief includes the visual thesis section as a visual anchor."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(style_bible_text=STYLE_TEXT)
    briefs = agent.build_scene_briefs(ctx)
    style_brief = next(b for b in briefs if b.element_type == "style")

    anchor_texts = [a.description for a in style_brief.visual_anchors]
    assert any("controlled world" in t.lower() for t in anchor_texts)


def test_style_brief_none_text_is_handled(tmp_path: Path) -> None:
    """style_bible_text=None → empty brief, is_ready=True (no warnings)."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(style_bible_text=None)
    briefs = agent.build_scene_briefs(ctx)
    style_brief = next(b for b in briefs if b.element_type == "style")

    assert style_brief.negative_constraints == []
    assert style_brief.visual_anchors == []
    assert style_brief.is_ready is True


# ---------------------------------------------------------------------------
# Cross-brief invariants
# ---------------------------------------------------------------------------


def test_all_briefs_model_guidance_required(tmp_path: Path) -> None:
    """Every brief, regardless of element type, has model_guidance_required=True."""
    repo = _make_repo(
        tmp_path, props={"PROP001": PROP001}, wardrobe={"WD001": WD001}
    )
    agent = NeutralBriefAgent(repo)
    ctx = _context(
        scene_id="SC0003",
        characters={"C01": CHAR_C01},
        location=LOC001,
        props={"PROP001": PROP001},
        wardrobe={"WD001": WD001},
        style_bible_text=STYLE_TEXT,
    )
    briefs = agent.build_scene_briefs(ctx)
    for brief in briefs:
        assert brief.model_guidance_required is True, (
            f"{brief.element_id} has model_guidance_required=False"
        )


def test_build_scene_briefs_produces_all_element_types(tmp_path: Path) -> None:
    """build_scene_briefs returns one brief per element type present."""
    repo = _make_repo(
        tmp_path, props={"PROP001": PROP001}, wardrobe={"WD001": WD001}
    )
    agent = NeutralBriefAgent(repo)
    ctx = _context(
        scene_id="SC0003",
        characters={"C01": CHAR_C01},
        location=LOC001,
        props={"PROP001": PROP001},
        wardrobe={"WD001": WD001},
        style_bible_text=STYLE_TEXT,
    )
    briefs = agent.build_scene_briefs(ctx)
    types = {b.element_type for b in briefs}

    assert "character" in types
    assert "location" in types
    assert "prop" in types
    assert "wardrobe" in types
    assert "style" in types


def test_style_always_included_when_no_other_elements(tmp_path: Path) -> None:
    """Style brief is always present even when scene has no elements."""
    agent = NeutralBriefAgent(tmp_path)
    ctx = _context(style_bible_text=STYLE_TEXT)
    briefs = agent.build_scene_briefs(ctx)

    assert any(b.element_type == "style" for b in briefs)
    assert len(briefs) == 1  # only style


# ---------------------------------------------------------------------------
# Integration — real SC0003
# ---------------------------------------------------------------------------


def test_sc0003_integration_brief_types() -> None:
    """Integration: SC0003 produces character, location, prop, wardrobe, style briefs."""
    source_agent = SourceContextAgent(REPO_ROOT)
    brief_agent = NeutralBriefAgent(REPO_ROOT)

    context = source_agent.build("SC0003")
    assert not context.escalate, "SC0003 escalated unexpectedly"

    briefs = brief_agent.build_scene_briefs(context)
    types = {b.element_type for b in briefs}

    assert "character" in types
    assert "location" in types
    assert "prop" in types
    assert "wardrobe" in types
    assert "style" in types


def test_sc0003_prop001_continuity_state_at_sc0003() -> None:
    """PROP001 brief for SC0003 has white-plastic continuity state."""
    source_agent = SourceContextAgent(REPO_ROOT)
    brief_agent = NeutralBriefAgent(REPO_ROOT)

    context = source_agent.build("SC0003")
    briefs = brief_agent.build_scene_briefs(context)

    prop_brief = next((b for b in briefs if b.element_id == "PROP001"), None)
    assert prop_brief is not None, "PROP001 brief not found"
    assert prop_brief.continuity_state is not None
    assert "white plastic" in prop_brief.continuity_state.lower()
    assert prop_brief.is_ready is True


def test_sc0003_all_briefs_have_model_guidance_required() -> None:
    source_agent = SourceContextAgent(REPO_ROOT)
    brief_agent = NeutralBriefAgent(REPO_ROOT)

    context = source_agent.build("SC0003")
    briefs = brief_agent.build_scene_briefs(context)

    for brief in briefs:
        assert brief.model_guidance_required is True


def test_sc0003_all_visual_anchors_have_source_fields() -> None:
    """Every visual anchor in a real SC0003 brief has a non-empty source_field."""
    source_agent = SourceContextAgent(REPO_ROOT)
    brief_agent = NeutralBriefAgent(REPO_ROOT)

    context = source_agent.build("SC0003")
    briefs = brief_agent.build_scene_briefs(context)

    for brief in briefs:
        for anchor in brief.visual_anchors:
            assert anchor.source_field, (
                f"Empty source_field in {brief.element_type}.{brief.element_id}: "
                f"{anchor.description[:60]}"
            )


def test_sc0003_negative_constraints_include_style_rules() -> None:
    """Element briefs for SC0003 include style bible constraints in negative_constraints."""
    source_agent = SourceContextAgent(REPO_ROOT)
    brief_agent = NeutralBriefAgent(REPO_ROOT)

    context = source_agent.build("SC0003")
    briefs = brief_agent.build_scene_briefs(context)

    # At least one element brief (not style) should have style constraints
    element_briefs = [b for b in briefs if b.element_type != "style"]
    assert element_briefs, "No element briefs generated"

    found_style_constraint = False
    for brief in element_briefs:
        joined = "\n".join(brief.negative_constraints).lower()
        if "neon" in joined or "teal-orange" in joined or "do not drift" in joined:
            found_style_constraint = True
            break

    assert found_style_constraint, (
        "No element brief contains style bible constraints"
    )
