from __future__ import annotations

from pathlib import Path

from scripts.agents.adapters.midjourney import MidjourneyAdapter
from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor


def _brief() -> NeutralBrief:
    return NeutralBrief(
        scene_id="SC0001",
        element_type="character",
        element_id="C01",
        element_name="Nadia Vale",
        visual_anchors=[VisualAnchor(description="Lean upright posture in cold daylight corridor.", source_field="x")],
        negative_constraints=["neon cyberpunk lighting"],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        prompt_subject_label="Nadia",
        planning_aliases=("Nadia Vale",),
        aesthetic_pack_refs=("VALE_DOMESTIC_RESTRAINT",),
    )


def test_raw_mode_in_generation_params_uses_raw_not_style_raw():
    adapter = MidjourneyAdapter(Path("."))
    params = adapter._generation_params(_brief())
    assert params["raw_mode"] == "--raw"
    assert "--style raw" not in str(params)


def test_sref_appended_only_when_snapshot_supports_style_reference():
    adapter = MidjourneyAdapter(Path("."), model_guidance_mode="dynamic_snapshot")
    adapter._resolve_model = lambda target: {"capabilities": {"supports_style_reference": True}}  # type: ignore[attr-defined]
    adapter._find_sref_seed = lambda refs: "vale_seed_001"  # type: ignore[attr-defined]
    params = adapter._extra_generation_params(_brief())
    assert params.get("style_reference") == "--sref vale_seed_001"


def test_sref_skipped_when_capability_false():
    adapter = MidjourneyAdapter(Path("."), model_guidance_mode="dynamic_snapshot")
    adapter._resolve_model = lambda target: {"capabilities": {"supports_style_reference": False}}  # type: ignore[attr-defined]
    adapter._find_sref_seed = lambda refs: "vale_seed_001"  # type: ignore[attr-defined]
    params = adapter._extra_generation_params(_brief())
    assert "style_reference" not in params


def test_sref_skipped_when_pack_has_no_seed():
    adapter = MidjourneyAdapter(Path("."), model_guidance_mode="dynamic_snapshot")
    adapter._resolve_model = lambda target: {"capabilities": {"supports_style_reference": True}}  # type: ignore[attr-defined]
    adapter._find_sref_seed = lambda refs: None  # type: ignore[attr-defined]
    params = adapter._extra_generation_params(_brief())
    assert "style_reference" not in params


def test_natural_language_template_v81():
    adapter = MidjourneyAdapter(Path("."))
    text = adapter._build_prompt_text(_brief())
    assert "Create a cinematic image of Nadia." in text
    assert "," not in text[:40]  # starts sentence-first, not comma-clause


def test_word_count_soft_warning_only_not_truncation():
    adapter = MidjourneyAdapter(Path("."))
    anchors = [
        VisualAnchor(description=" ".join(["precise"] * 20), source_field=f"x{i}")
        for i in range(5)
    ]
    b = NeutralBrief(**{**_brief().__dict__, "visual_anchors": anchors})
    text = adapter._build_prompt_text(b)
    # Should not clamp to legacy 60 in the new template path
    assert len(text.split()) > 40
    assert len(text.split()) <= 200
