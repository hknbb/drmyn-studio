from __future__ import annotations

from pathlib import Path

from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter
from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor


def _brief() -> NeutralBrief:
    return NeutralBrief(
        scene_id="SC0001",
        element_type="character",
        element_id="C01",
        element_name="Nadia Vale",
        visual_anchors=[VisualAnchor(description="Lean upright posture in filtered daylight.", source_field="x")],
        negative_constraints=["neon tones", "cartoon styling"],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        prompt_subject_label="Nadia",
        planning_aliases=("Nadia Vale",),
        preserve_list=("wrist scar", "muted neutral palette"),
    )


def test_labeled_segments_in_prompt():
    adapter = ChatGPTImageAdapter(Path("."))
    text = adapter._build_prompt_text(_brief())
    assert "Scene:" in text and "Subject:" in text and "Details:" in text and "Constraints:" in text
    assert "Preserve:" in text
    assert "wrist scar" in text


def test_multi_panel_only_when_snapshot_supports():
    adapter = ChatGPTImageAdapter(Path("."), model_guidance_mode="dynamic_snapshot")
    adapter._supports_multi_panel = lambda: True  # type: ignore[method-assign]
    b = _brief()
    b = NeutralBrief(**{**b.__dict__, "expected_output_layout": "multi_panel", "panel_prompts": ("Panel A action", "Panel B action")})
    text = adapter._build_prompt_text(b)
    assert "Panel 1:" in text and "Panel 2:" in text


def test_multi_panel_falls_back_when_capability_false():
    adapter = ChatGPTImageAdapter(Path("."), model_guidance_mode="dynamic_snapshot")
    adapter._supports_multi_panel = lambda: False  # type: ignore[method-assign]
    b = _brief()
    b = NeutralBrief(**{**b.__dict__, "expected_output_layout": "multi_panel", "panel_prompts": ("Panel A action", "Panel B action")})
    text = adapter._build_prompt_text(b)
    assert "Panel 1:" not in text
    assert "Scene:" in text and "Subject:" in text


def test_no_provider_model_version_hardcoded():
    path = Path("scripts/agents/adapters/chatgpt_image.py")
    src = path.read_text(encoding="utf-8").lower()
    assert "gpt-image-2" not in src
    assert "dall-e-3" not in src
